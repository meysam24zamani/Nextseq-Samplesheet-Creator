# nextseq-samplesheet-creator

Create the samplesheet (`SampleSheet.csv`) for NextSeq machines.

## Changelogs

### v3.0

Released 29-04-2019. Check format of input CSV file and remove `subprocess`
calls. Changes introduced:

* Add 8 new input files for testing (7 for failed and 1 for successful executions)
* Raise errors for missing/invalid header names, empty cells, and invalid sequencing indexes.
* Add 2 custom exceptions: `Bcl2fastqEmptyCellError` and `Bcl2fastqIndexError`.
* Create missing directories to fix `FileNotFoundError` on `df.to_csv()` operation when saving to a directory that doesn't exist.
* Remove `dos2unix_conversion` function (the bcl2fastq pipeline already handles this).
* Replace `subprocess` for `fileinput` call in `concatenate_files()` method.

### v2.0

The one that runs as a CWL step. Input parameters are:

* `--input-file`
* `--headers-file`
* `--output-file`

### v1.0

The one that does a rename of the input to be able to save the final output to the initial input filename. Input parameters are:

* `--input-dir`
* `--headers-file`
