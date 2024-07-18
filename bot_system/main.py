from bot_system.src.lib.run_on_main import RunOnMainThread
from bot_system.src.pepper_gpt import PepperGPT

prompter = PepperGPT(mute=False, no_cost=False, no_pepper=True, context_data_path="bot_system/data")

try:
    while True:
        RunOnMainThread.fetch_and_execute_callback()
except KeyboardInterrupt:
    prompter.dispose()
    print("Exiting")

print("Done")
