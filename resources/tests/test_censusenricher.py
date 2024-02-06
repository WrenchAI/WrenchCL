import pytest
import pandas as pd
from uszipcode import SearchEngine
import pandas.testing as pdt
from WrenchCL import CensusEnricher  # replace 'your_module' with the actual module name

@pytest.fixture
def census_enricher():
    return CensusEnricher()

@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        'zip': [12345, 67890, 10111],
        'other_column': [1, 2, 3]
    })

def test_initialization(census_enricher):
    assert isinstance(census_enricher.search_engine, SearchEngine)
    assert census_enricher.zip_info_df.empty

def test_enrich_with_zip_info(census_enricher, sample_dataframe):
    enriched_df = census_enricher.enrich_with_zip_info(sample_dataframe)
    assert not enriched_df.empty
    assert 'zip' in enriched_df.columns
    # Add more assertions based on expected enriched columns

def test_collect_zip_data(census_enricher, sample_dataframe):
    zip_data = census_enricher._collect_zip_data(sample_dataframe, 'zip')
    assert isinstance(zip_data, list)
    # Assert the length of the list or contents based on your data

def test_get_zip_data(census_enricher):
    zip_data = census_enricher._get_zip_data(12345)
    assert isinstance(zip_data, dict)  # or None if zip code is not valid

def test_process_zip_info(census_enricher, sample_dataframe):
    census_enricher.enrich_with_zip_info(sample_dataframe)
    assert 'housing_density' in census_enricher.zip_info_df.columns
    # Further assertions based on expected transformations

def test_removal_of_existing_state_county_columns(census_enricher, sample_dataframe):
    sample_dataframe['state'] = 'Existing State'
    sample_dataframe['county'] = 'Existing County'
    enriched_df = census_enricher.enrich_with_zip_info(sample_dataframe)
    assert 'state' not in enriched_df.columns
    assert 'county' not in enriched_df.columns

def test_empty_dataframe(census_enricher):
    empty_df = pd.DataFrame()
    result = census_enricher.enrich_with_zip_info(empty_df)
    assert ValueError

def test_missing_zip_column(census_enricher):
    df_no_zip = pd.DataFrame({'other_column': [1, 2, 3]})
    with pytest.raises(KeyError):
        census_enricher.enrich_with_zip_info(df_no_zip)

def test_non_numeric_zip(census_enricher):
    non_numeric_df = pd.DataFrame({'zip': [7834920, 'xyz'], 'other_column': [1, 2]})
    enriched_df = census_enricher.enrich_with_zip_info(non_numeric_df)
    pdt.assert_frame_equal(enriched_df, non_numeric_df, check_dtype=False)

def test_incorrect_data_type(census_enricher, sample_dataframe):
    incorrect_df = pd.DataFrame({'zip': ['not a number', True], 'other_column': [1, 2]})
    enriched_df = census_enricher.enrich_with_zip_info(incorrect_df)
    pdt.assert_frame_equal(enriched_df, incorrect_df, check_dtype=False)

