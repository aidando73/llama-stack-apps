
```bash
# Add to .bashrc
export PATH=~/Library/Android/sdk/tools:$PATH
export PATH=~/Library/Android/sdk/platform-tools:$PATH

adb reverse tcp:5000 tcp:5000
adb reverse --list
```
