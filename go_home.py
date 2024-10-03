from skyhunter import IoptronMount
from config import port

# Go to zero position
mount = IoptronMount(port)
mount.goto_zero_position()