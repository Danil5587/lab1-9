"""
Лабораторная работа №12 — вариант 5.
Асинхронная обработка заявок в деканат через asyncio.PriorityQueue.
Python 3.11+
"""
from __future__ import annotations

import asyncio
import time
from collections import Counter
from dataclasses import dataclass
from itertools import count
from typing import Any

PRIORITY = {"срочная": 0, "обычная": 1, "низкая": 2}
SENTINEL_PRIORITY = 10_000


@dataclass(frozen=True)
class Request:
    number: int
    category: str
    text: str
    priority: str


@dataclass(frozen=True, order=True)
class QueueItem:
    priority: int
    sequence: int
    request: Request | None


def validate_request(request: Request) -> None:
    if not isinstance(request.number, int) or request.number <= 0:
        raise ValueError("Номер заявки должен быть положительным целым числом")
    if not request.category.strip():
        raise ValueError("Не указана категория заявки")
    if not request.text.strip():
        raise ValueError("Описание заявки не должно быть пустым")
    if request.priority not in PRIORITY:
        raise ValueError("Приоритет должен быть: срочная, обычная или низкая")


async def handle_request(request: Request) -> dict[str, Any]:
    """Имитирует асинхронную обработку заявки."""
    await asyncio.sleep(0.15)
    validate_request(request)
    return {
        "number": request.number,
        "category": request.category,
        "text": request.text,
        "priority": request.priority,
        "status": "решена",
    }


async def producer(
    queue: asyncio.PriorityQueue,
    requests: list[Request],
    worker_count: int,
) -> None:
    sequence = count()
    for request in requests:
        await asyncio.sleep(0.03)
        await queue.put(
            QueueItem(PRIORITY.get(request.priority, 99), next(sequence), request)
        )
        print(f"[ПРОИЗВОДИТЕЛЬ] Добавлена заявка №{request.number}")

    # Большое значение приоритета гарантирует, что сигналы завершения
    # будут извлечены после всех заявок, находящихся в очереди.
    for _ in range(worker_count):
        await queue.put(QueueItem(SENTINEL_PRIORITY, next(sequence), None))


async def consumer(
    name: str,
    queue: asyncio.PriorityQueue,
    solved: list[dict[str, Any]],
    errors: list[str],
    dequeue_order: list[int],
) -> None:
    while True:
        item: QueueItem = await queue.get()
        try:
            if item.request is None:
                print(f"[{name}] Завершение работы")
                return

            request = item.request
            dequeue_order.append(request.number)
            print(
                f"[{name}] Получена заявка №{request.number} "
                f"(приоритет: {request.priority})"
            )
            try:
                async with asyncio.timeout(2):
                    result = await handle_request(request)
                solved.append(result)
                print(f"[{name}] Заявка №{request.number} решена")
            except (ValueError, TimeoutError) as error:
                message = f"Заявка №{request.number}: {error}"
                errors.append(message)
                print(f"[ОШИБКА] {message}")
        finally:
            queue.task_done()


async def main() -> None:
    requests = [
        Request(101, "Документы", "Справка об обучении", "обычная"),
        Request(102, "Стипендия", "Не поступила стипендия", "срочная"),
        Request(103, "Расписание", "Уточнить расписание экзамена", "низкая"),
        Request(104, "Общежитие", "Проблема с заселением", "срочная"),
        Request(105, "Документы", "Исправить данные в справке", "обычная"),
        Request(106, "Другое", " ", "низкая"),  # пример ошибочной заявки
    ]

    worker_count = 2
    queue: asyncio.PriorityQueue[QueueItem] = asyncio.PriorityQueue(maxsize=3)
    solved: list[dict[str, Any]] = []
    errors: list[str] = []
    dequeue_order: list[int] = []
    started = time.perf_counter()

    workers = [
        asyncio.create_task(
            consumer(f"Оператор-{i}", queue, solved, errors, dequeue_order)
        )
        for i in range(1, worker_count + 1)
    ]

    await producer(queue, requests, worker_count)
    await queue.join()
    await asyncio.gather(*workers)

    elapsed = time.perf_counter() - started
    category_stats = Counter(item["category"] for item in solved)

    print("\n" + "=" * 48)
    print("ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 48)
    print(f"Всего поступило заявок: {len(requests)}")
    print(f"Успешно решено: {len(solved)}")
    print(f"Ошибок: {len(errors)}")
    print(f"Время выполнения: {elapsed:.2f} сек.")
    print("\nРешённые заявки по категориям:")
    if category_stats:
        for category, amount in sorted(category_stats.items()):
            print(f"  {category}: {amount}")
    else:
        print("  Нет решённых заявок")

    print("\nПорядок получения заявок операторами:")
    print("  " + " -> ".join(map(str, dequeue_order)))
    if errors:
        print("\nСообщения об ошибках:")
        for error in errors:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())
