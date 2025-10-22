**A piped progress bar for sox to convert 10-bit 40msps DdD captures.**

Create stat file with ETA
`python progress_lds.py "%INPUT_LDS%" --stat`
Run this in order to create the stat file using sox, and this has a progress bar estimating using the file size, tends to run at the speed of the hard drive.

Compress with ETA
`ld-lds-converter -i "%INPUT_LDS%" | [sox command] 2>&1 | python progress_lds.py "%INPUT_LDS%" --progress`

Pipe the terminal output of sox into this python code and it interprets it to give a nice progress bar with ETA. Takes the duration length from the stat txt and *1.6 for the 10-bit to 16-bit conversion ld-lds-converter does, and /1000 because we're telling sox to assume our files are in Ksps instead of Msps.

Added my batch file for clarity, although I'm running this in a conda environment, YMMV.
