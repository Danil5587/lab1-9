import asyncio
import unittest

from main import (
    PRIORITY,
    SENTINEL_PRIORITY,
    QueueItem,
    Request,
    consumer,
    handle_request,
    producer,
    validate_request,
)


class RequestValidationTests(unittest.TestCase):
    def test_valid_request(self):
        validate_request(Request(1, "Документы", "Нужна справка", "обычная"))

    def test_invalid_number(self):
        with self.assertRaises(ValueError):
            validate_request(Request(0, "Документы", "Нужна справка", "обычная"))

    def test_empty_category(self):
        with self.assertRaises(ValueError):
            validate_request(Request(1, " ", "Нужна справка", "обычная"))

    def test_empty_description(self):
        with self.assertRaises(ValueError):
            validate_request(Request(1, "Документы", " ", "обычная"))

    def test_unknown_priority(self):
        with self.assertRaises(ValueError):
            validate_request(Request(1, "Документы", "Справка", "сверхсрочная"))


class AsyncPipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_priority_order_in_queue(self):
        queue = asyncio.PriorityQueue()
        await queue.put(QueueItem(PRIORITY["обычная"], 0,
                                  Request(1, "А", "Текст", "обычная")))
        await queue.put(QueueItem(PRIORITY["срочная"], 1,
                                  Request(2, "Б", "Текст", "срочная")))
        first = await queue.get()
        self.assertEqual(first.request.number, 2)

    async def test_producer_adds_one_sentinel_per_worker(self):
        queue = asyncio.PriorityQueue()
        await producer(queue, [], 2)
        items = [await queue.get(), await queue.get()]
        self.assertEqual(sum(x.priority == SENTINEL_PRIORITY for x in items), 2)

    async def test_handle_request(self):
        result = await handle_request(
            Request(7, "Стипендия", "Проверить выплату", "срочная")
        )
        self.assertEqual(result["status"], "решена")
        self.assertEqual(result["number"], 7)

    async def test_consumer_records_validation_error_and_finishes(self):
        queue = asyncio.PriorityQueue()
        bad = Request(9, " ", "Описание", "обычная")
        await queue.put(QueueItem(PRIORITY["обычная"], 0, bad))
        await queue.put(QueueItem(SENTINEL_PRIORITY, 1, None))
        solved, errors, order = [], [], []
        await consumer("Тестовый оператор", queue, solved, errors, order)
        self.assertEqual(len(solved), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(order, [9])
        self.assertEqual(queue._unfinished_tasks, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
