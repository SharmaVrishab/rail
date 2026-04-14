"""Search for cheapest / most available dates across a date range.

Iterates over each date in [start_date, end_date] checking seat availability
and aggregates results into a sorted list.
"""

from datetime import date, timedelta

from rail.models.indian_railways.availability import AvailabilityFilters
from rail.models.indian_railways.base import DateAvailability, Quota, TrainClass
from rail.models.indian_railways.trains import TrainSearchFilters
from rail.search.availability import SearchAvailability
from rail.search.trains import SearchTrains

# Status priority for sorting (lower = better)
_STATUS_RANK = {
    "AVAILABLE": 0,
    "RAC": 1,
    "WL": 2,
    "REGRET": 3,
    "NOT AVAILABLE": 4,
    "UNKNOWN": 5,
}

# Maximum date range to scan in one call (Indian Railways opens ~120 days ahead)
MAX_DAYS = 120


class SearchDates:
    """Find availability and fares across a flexible date range for a train route."""

    def search(
        self,
        origin: str,
        destination: str,
        start_date: str,
        end_date: str,
        train_class: TrainClass,
        quota: Quota = Quota.GENERAL,
        train_number: str | None = None,
        sort_by_price: bool = True,
    ) -> list[DateAvailability]:
        """Scan dates and return availability for each.

        If a specific train_number is given, checks that train directly.
        Otherwise, picks the first train found on the first available date and
        uses it as the reference train for the whole date range.

        Args:
            origin: Origin station code.
            destination: Destination station code.
            start_date: Range start (YYYY-MM-DD).
            end_date: Range end (YYYY-MM-DD).
            train_class: Coach class to check.
            quota: Booking quota (default: GENERAL).
            train_number: Optional specific train to check.
            sort_by_price: Sort by fare (True) or by availability status.

        Returns:
            List of DateAvailability, one entry per date.
        """
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        # Cap the range
        if (end - start).days > MAX_DAYS:
            end = start + timedelta(days=MAX_DAYS)

        # Resolve train number if not provided
        if not train_number:
            train_number = self._resolve_train(origin, destination, start_date, train_class, quota)

        if not train_number:
            return []

        avail_searcher = SearchAvailability()
        results: list[DateAvailability] = []

        current = start
        while current <= end:
            date_str = current.isoformat()
            avail_filters = AvailabilityFilters(
                train_number=train_number,
                origin=origin,
                destination=destination,
                departure_date=date_str,
                train_class=train_class,
                quota=quota,
            )
            avail_list = avail_searcher.search(avail_filters)

            if avail_list:
                a = avail_list[0]
                results.append(
                    DateAvailability(
                        date=date_str,
                        train_number=train_number,
                        train_name="",
                        train_class=train_class,
                        quota=quota,
                        status=a.status,
                        available_count=a.available_count,
                        fare=a.fare,
                    )
                )
            else:
                results.append(
                    DateAvailability(
                        date=date_str,
                        train_number=train_number,
                        train_name="",
                        train_class=train_class,
                        quota=quota,
                        status="UNKNOWN",
                    )
                )

            current += timedelta(days=1)

        return self._sort(results, sort_by_price)

    def _resolve_train(
        self,
        origin: str,
        destination: str,
        date_str: str,
        train_class: TrainClass,
        quota: Quota,
    ) -> str | None:
        """Find the first train running between origin and destination.

        Args:
            origin: Origin station code.
            destination: Destination station code.
            date_str: Journey date (YYYY-MM-DD).
            train_class: Class filter.
            quota: Quota filter.

        Returns:
            Train number string, or None if none found.
        """
        filters = TrainSearchFilters(
            origin=origin,
            destination=destination,
            departure_date=date_str,
            train_class=train_class,
            quota=quota,
        )
        trains = SearchTrains().search(filters, top_n=1)
        return trains[0].train_number if trains else None

    def _sort(self, results: list[DateAvailability], by_price: bool) -> list[DateAvailability]:
        """Sort results by price or availability status.

        Args:
            results: Unsorted list.
            by_price: Sort by fare if True, else by status rank.

        Returns:
            Sorted list.
        """
        def _status_rank(r: DateAvailability) -> int:
            for key, rank in _STATUS_RANK.items():
                if r.status.upper().startswith(key):
                    return rank
            return 99

        if by_price:
            return sorted(
                results,
                key=lambda r: (r.fare is None, r.fare or 0),
            )
        return sorted(results, key=_status_rank)
