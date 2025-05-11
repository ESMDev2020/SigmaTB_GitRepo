# launch_streamlit.py
import os
import sys
import subprocess

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Path to your main app
main_app = os.path.join(current_dir, "p_01_SigmaTBMain_v2.py")

# Run the app with streamlit
streamlit_process = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", main_app],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True
)

# Print a message when the app starts
print(f"Streamlit app starting at: {main_app}")
print("Debug output from Streamlit:")

try:
    # Keep the process running and capture output
    while streamlit_process.poll() is None:
        # Print any output from Streamlit
        output = streamlit_process.stdout.readline()
        if output:
            print(output.strip())
except KeyboardInterrupt:
    # Handle Ctrl+C gracefully
    print("Stopping Streamlit...")
    streamlit_process.terminate()
finally:
    # Clean up
    streamlit_process.wait()