import pandas as pd


class Dataset:
    def __init__(self):
        _kosovo_businesses_path = "data/KosovoBusinesses.csv"

        kosovo_businesses = pd.read_csv(_kosovo_businesses_path)
        kosovo_businesses.drop("Unnamed: 0", axis=1, inplace=True)
        kosovo_businesses["RegistrationDate"] = pd.to_datetime(
            kosovo_businesses["RegistrationDate"], errors="coerce", dayfirst=True)
        kosovo_businesses.drop_duplicates(inplace=True)

        self.data = kosovo_businesses

    def number_new_per_period(self, freq="M"):
        number_new = self.data.groupby(pd.Grouper(key="RegistrationDate", freq=freq)).count()["Capital"]
        number_new = pd.DataFrame({"MonthEndDate": number_new.index, "NumberNew": number_new})
        number_new.reset_index(inplace=True, drop=True)
        return number_new

    def number_closed_per_period(self, freq="M"):
        number_closed = self.data[self.data["ClosingDate"].notna()].reset_index(drop=True)
        number_closed["ClosingDate"] = pd.to_datetime(number_closed["ClosingDate"])
        number_closed = number_closed.groupby(pd.Grouper(key="ClosingDate", freq=freq)).count()["Capital"]
        number_closed = pd.DataFrame({"MonthEndDate": number_closed.index, "NumberClosed": number_closed})
        number_closed.reset_index(inplace=True, drop=True)
        return number_closed

    def number_registered_closed(self, freq="M"):
        number_new = self.number_new_per_period(freq=freq)
        number_closed = self.number_closed_per_period(freq=freq)
        return number_new.merge(number_closed, on="MonthEndDate", how="left").fillna(0)

    def failure_rate_by_region(self, min_date, max_date):
        # Filter for dates
        mask = (self.data["RegistrationDate"] >= min_date) & (self.data["RegistrationDate"] <= max_date)
        _data = self.data.loc[mask]
        # Number Registered
        registered = _data.groupby("Region").size()
        failed = _data.loc[_data["Failed"] == 1].groupby("Region").size()
        registered = pd.DataFrame({"Region": registered.index, "NumberRegistered": registered.values})
        # Number Failed
        failed = pd.DataFrame({"Region": failed.index, "NumberFailed": failed.values})
        # Merge
        _failure_rate_by_region = pd.merge(registered, failed, on="Region",
                                           how="left")  # On left to prevent division by 0
        _failure_rate_by_region["NumberFailed"].fillna(0, inplace=True)
        _failure_rate_by_region["FailureRate"] = _failure_rate_by_region["NumberFailed"] / _failure_rate_by_region[
            "NumberRegistered"]
        return _failure_rate_by_region

    def group_by(self, col, freq="M"):
        datasets = []
        for v in self.data[col].unique():
            filtered_data = self.data.loc[self.data[col] == v]
            number_new = filtered_data.groupby(
                pd.Grouper(key="RegistrationDate", freq=freq)
            ).count()["Capital"]
            number_new = pd.DataFrame({"MonthEndDate": number_new.index, "NumberNew": number_new})
            number_new.reset_index(inplace=True, drop=True)

            number_closed = filtered_data[filtered_data["ClosingDate"].notna()].reset_index(drop=True)
            number_closed["ClosingDate"] = pd.to_datetime(number_closed["ClosingDate"])
            number_closed = number_closed.groupby(pd.Grouper(key="ClosingDate", freq=freq)).count()["Capital"]
            number_closed = pd.DataFrame({"MonthEndDate": number_closed.index, "NumberClosed": number_closed})
            number_closed.reset_index(inplace=True, drop=True)

            number_new.merge(number_closed, on="MonthEndDate", how="left").fillna(0)

            datasets.append(number_new)
        return datasets
