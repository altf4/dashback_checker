# dashback_checker
Checks to see if SLP replays are doing dashbacks correctly

# What counts as a "Successful UCF Dashback"
Starting from a standing position (frame i), you need to satisfy four conditions on frame i+2:
- move at least 76 raw units
- pass the +-64 raw unit barrier
- move >0.9375 total processed x units
- move past the +/- 0.8 processed barrier

Note: This script actually does check for both dash-forward AND dash-back. But we just call them collectively "dashbacks" for no good reason.

# How to run

Grab the dependencies:

`python -m pip install -r requirements.txt`

Then run it:

`python dashback_checker.py`

This will by default use the sample SLP's included in `test_data/`, which are the Genesis X top 8 matches.

To use your own SLPs, provide the `--file` arg:

`python dashback_checker.py --file PATH_TO_SLP_DIRECTORY/`

# Output

You'll see it output the total number of successes and failures, it'll look something like this:

```
Successful dashbacks: 29037
Failed dashbacks:  0
```