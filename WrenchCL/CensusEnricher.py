import numpy as np
import pandas as pd
from WrenchCL import wrench_logger
from uszipcode import SearchEngine


class CensusEnricher:
    def __init__(self):
        self.search_engine = SearchEngine()
        self.zip_info_df = pd.DataFrame()
        wrench_logger.info("ZipCodeEnricher initialized")


    def __call__(self, df : pd.DataFrame, zip_column='zip', process_info=False):
        if df.empty:
            wrench_logger.error("Empty Dataframe has been passed as an argument")
            raise ValueError
        zip_column = zip_column.lower().strip()
        df.columns = df.columns.str.lower().str.strip()
        enriched_df = self.enrich_with_zip_info(df, zip_column)

        if process_info:
            self.process_zip_info()

        return enriched_df

    def enrich_with_zip_info(self, df, zip_column='zip'):
        wrench_logger.info(f"Starting the enrichment process for dataframe with length {len(df)}")
        deduplicated_df = df.drop_duplicates(subset=zip_column, keep='first')

        zip_data_list = self._collect_zip_data(deduplicated_df, zip_column)

        self.zip_info_df = pd.DataFrame(zip_data_list)
        self.process_zip_info()

        self._prepare_dataframes_for_merge(df)
        merged_df = self._merge_dataframes(df, zip_column)
        wrench_logger.info(f"Enrichment process completed dataframe shape {len(merged_df)}")

        return merged_df

    def _collect_zip_data(self, df, zip_column):
        wrench_logger.info("Collecting zip data")
        zip_data_list = []
        for idx, row in df.iterrows():
            if row[zip_column] is not None:
                zip_data = self._get_zip_data(row[zip_column])
                if zip_data:
                    zip_data_list.append(zip_data)
                else:
                    wrench_logger.debug(f"No zip found for {row[zip_column]}")
        return zip_data_list

    def _get_zip_data(self, zip_code):
        z = self.search_engine.by_zipcode(zip_code)
        if z:
            return dict(z.items())
        return None

    def _prepare_dataframes_for_merge(self, df):
        wrench_logger.info("Preparing dataframes for merge")

        if not self.zip_info_df.empty and not df.empty:
            # Check for 'state' and 'county' columns in a case-insensitive manner
            lower_columns = df.columns.str.lower()
            if 'state' in lower_columns:
                wrench_logger.info("Dropping existing 'state' column")
                df.drop('state', axis=1, inplace=True)
            if 'county' in lower_columns:
                wrench_logger.info("Dropping existing 'county' column")
                df.drop('county', axis=1, inplace=True)

            df['zip'] = pd.to_numeric(df['zip'], errors='coerce').astype('Int64')
            self.zip_info_df = self.zip_info_df[pd.to_numeric(self.zip_info_df['zipcode'], errors='coerce').notna()]
            self.zip_info_df['zipcode'] = self.zip_info_df['zipcode'].astype('Int64')
        else:
            self.zip_info_df = df


    def _merge_dataframes(self, df, zip_column):
        wrench_logger.info("Merging dataframes")

        if not self.zip_info_df.empty and "zipcode" in self.zip_info_df.columns:
            merged_df = pd.merge(df, self.zip_info_df, left_on=zip_column, right_on='zipcode', how='left')
            merged_df.drop('zipcode', axis=1, inplace=True)
            merged_df = merged_df.replace({pd.NA: None})
            self._prepend_columns(merged_df)
            return merged_df
        else:
            merged_df = df
            return merged_df

    def _prepend_columns(self, df):
        wrench_logger.info("Prepending 'census_' to zip enriched columns")
        zip_columns = [col for col in df.columns if col in self.zip_info_df.columns]
        df.rename(columns={col: f"dm_census_{col}" for col in zip_columns}, inplace=True)

    def process_zip_info(self):
        # Remove specified columns
        if not self.zip_info_df.empty:
            columns_to_remove = ['zipcode_type', 'post_office_city', 'common_city_list',
                                 'timezone', 'area_code_list', 'radius_in_miles',
                                 'bounds_west', 'bounds_east', 'bounds_north', 'bounds_south']
            self.zip_info_df.drop(columns=columns_to_remove, inplace=True, errors='ignore')

            # Calculate housing density
            self.zip_info_df['housing_density'] = self.zip_info_df['housing_units'] / self.zip_info_df['land_area_in_sqmi']

            # Calculate family size
            self.zip_info_df['family_size'] = self.zip_info_df['population'] / self.zip_info_df['occupied_housing_units']

            # Calculate the percentage of housing value covered by median household income
            self.zip_info_df['percent_home_value_covered_by_income'] = (self.zip_info_df['median_household_income'] / self.zip_info_df['median_home_value']) * 100

            # Calculate income per family member
            self.zip_info_df['income_per_family_member'] = self.zip_info_df['median_household_income'] / self.zip_info_df['family_size']

            # Handle potential divisions by zero
            self.zip_info_df.replace([np.inf, -np.inf], np.nan, inplace=True)
            self.zip_info_df.fillna(0, inplace=True)
        else:
            wrench_logger.error(f"Empty Dataframe returned selected zip column did not contain any zip codes. (Default zip column = Zip or zip)")

# Example usage
# Assuming 'result_df' is your DataFrame
# zip_enricher = ZipCodeEnricher()
# merged_df = zip_enricher.enrich_with_zip_info(result_df)
# merged_df.to_csv("zipinfo.csv")
