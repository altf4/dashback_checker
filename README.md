# dashback_checker
Checks to see if SLP replays are doing dashbacks correctly

# What counts as a "Successful UCF Dashback"

To do a UCF dash back, you need to start by exiting or passing the processed dead x zone (0.2875), then:
1. move past the +/- 0.8 processed barrier
2. move at least 76 raw units

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
Successful dashbacks: 1266
Failed dashbacks:  0
```