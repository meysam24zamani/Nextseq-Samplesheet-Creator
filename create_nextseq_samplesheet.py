#!/usr/bin/env python3
import argparse
import fileinput
import logging
import sys
import traceback
from pathlib import Path

import pandas as pd

AGILENT_SURESELECT_INDEXES = {
    "P7_i1":  "TAAGGCGA", "P7_i2":  "CGTACTAG", "P7_i3":  "AGGCAGAA",
    "P7_i4":  "TCCTGAGC", "P7_i5":  "GTAGAGGA", "P7_i6":  "TAGGCATG",
    "P7_i7":  "CTCTCTAC", "P7_i8":  "CAGAGAGG", "P7_i9":  "GCTACGCT",
    "P7_i10": "CGAGGCTG", "P7_i11": "AAGAGGCA", "P7_i12": "GGACTCCT",
    "P5_i13": "GCGATCTA", "P5_i14": "ATAGAGAG", "P5_i15": "AGAGGATA",
    "P5_i16": "TCTACTCT", "P5_i17": "CTCCTTAC", "P5_i18": "TATGCAGT",
    "P5_i19": "TACTCCTT", "P5_i20": "AGGCTTAG"
}


class Bcl2fastqEmptyCellError(ValueError):
    """Custom ValueError if any dataframe cell is empty."""
    pass


class Bcl2fastqIndexError(ValueError):
    """Custom ValueError if any index (from Agilent kit, etc.) is invalid."""
    pass


def concatenate_files(headers_file: str, output_file: str) -> str:
    """Concatenate headers CSV + ouput CSV files.

    The input parameter "output_file" contains the second part of text that
    needs to be combined. That's why it's renamed to a temp file, and its
    original filename is used for the output of the concatenated text.
    """
    logging.info(f"Concatenating '{headers_file}' with '{output_file}'...")
    tmp_file = Path(output_file).with_suffix(".tmp.csv")  # make tmp_file
    Path(output_file).rename(tmp_file)
    # Concatenate with fileinput library (https://stackoverflow.com/a/13613527)
    with open(output_file, 'w') as fout, fileinput.input([headers_file, tmp_file]) as fin:
        for line in fin:
            fout.write(line)
    tmp_file.unlink()  # remove tmp_file
    logging.info(f"Finished concatenation")
    return output_file


def create_output_file(headers_file: str, samplesheet_file: str, output_file: str) -> str:
    """Create the final output file with headers.

    Different steps are involved here:

      1. Read the input CSV file
      2. Keep only some of its columns
      3. Perform some checks on it (empty values, invalid index names)
      4. Create 2 new columns (Index1Sequence/Index2Sequence) with values based on AGILENT_SURESELECT_INDEXES
      5. Reorder all columns
      6. Concatenate the resulting CSV file with the headers CSV file (and create intermediate parent dirs if they don't exist)
      7. Return the concatenated file as a path
    """
    logging.info("Creating output file...")

    df = pd.read_csv(str(samplesheet_file), index_col="SampleID")

    # Keep only some of the columns
    df = df[["Name", "Index1Name", "Index2Name"]]

    # Check for empty values in index or in dataframe (handled differently)
    if df.index.hasnans or df.isnull().any().any():
        raise Bcl2fastqEmptyCellError()

    # Check for valid sequencing indexes (checks if all values for Index1Name/Index2Name
    # are found in dict keys; if there is any value that's not in dict it returns False)
    if not df["Index1Name"].isin(AGILENT_SURESELECT_INDEXES.keys()).all():
        raise Bcl2fastqIndexError()
    if not df["Index2Name"].isin(AGILENT_SURESELECT_INDEXES.keys()).all():
        raise Bcl2fastqIndexError()

    # Create the columns Index1Sequence and Index2Sequence from dictionary
    df["Index1Sequence"] = df["Index1Name"].map(AGILENT_SURESELECT_INDEXES)
    df["Index2Sequence"] = df["Index2Name"].map(AGILENT_SURESELECT_INDEXES)

    # Reorder columns
    df = df[["Name", "Index1Name", "Index1Sequence", "Index2Name", "Index2Sequence"]]
    df.columns = ["Sample_Name", "I7_Index_ID", "index", "I5_Index_ID", "index2"]
    df.index = df.index.rename("Sample_ID")

    # Concatenate headers and output_file (intermediate file) into one CSV file
    if Path(output_file).parent.exists() is False:
        Path(output_file).parent.mkdir(parents=True)
    df.to_csv(output_file)
    output_file = concatenate_files(headers_file, output_file)

    logging.info(f"Output file saved to '{output_file}'")
    return output_file


def print_traceback(ex: Exception) -> str:
    """Fetch and format the traceback associated with the given exception.

    Taken from https://realpython.com/the-most-diabolical-python-antipattern/.
    """
    tb_lines = traceback.format_exception(ex.__class__, ex, ex.__traceback__)
    tb_text = ''.join(tb_lines)
    return tb_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Script to run the SampleSheet creator for NextSeq machines.")
    parser.add_argument(
        "--input-file",
        required=True,
        help=f"Path to the input file to process")
    parser.add_argument(
        "--output-file",
        required=True,
        help=f"Path to the output file")
    parser.add_argument(
        "--headers-file",
        required=True,
        help="Path to the file with the headers that will be added to the output file (in CSV format)")
    args = parser.parse_args()

    logging.info(f"Starting script '{__file__}'")

    create_output_file(
        headers_file=args.headers_file,
        samplesheet_file=args.input_file,
        output_file=args.output_file)

    logging.info(f"Finished script '{__file__}'")


if __name__ == "__main__":
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s [%(levelname)s] -- %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout)
    try:
        main()
    except Bcl2fastqEmptyCellError as err:
        logging.error("[CSV FORMAT] The CSV file contains cells with empty values.")
        sys.exit(1)
    except Bcl2fastqIndexError as err:
        logging.error(
            "[CSV FORMAT] The CSV file contains indexes not defined in the pipeline, "
            f"the valid indexes are: {', '.join(AGILENT_SURESELECT_INDEXES.keys())}."
        )
        sys.exit(1)
    except (ValueError, KeyError) as err:
        logging.error(
            "[CSV FORMAT] The CSV file must contain the following "
            "column names: SampleID, Name, Index1Name, Index2Name. "
            f"The error message is: {err}"
        )
        sys.exit(1)
    except Exception as err:
        logging.error(f"Error in execution! {print_traceback(err)}")
        sys.exit(1)
