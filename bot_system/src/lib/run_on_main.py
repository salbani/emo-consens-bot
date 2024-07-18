import queue


class RunOnMainThread:
    """ A utility class for scheduling and executing functions on the main thread. """

    callback_queue = queue.Queue()

    @staticmethod
    def schedule(func_to_call_from_main_thread):
        """
        Schedule a function to be called from the main thread.

        Args:
            func_to_call_from_main_thread (callable): The function to be called from the main thread.
        """
        RunOnMainThread.callback_queue.put(func_to_call_from_main_thread)

    @staticmethod
    def fetch_and_execute_callback():
        """ Fetches a function from the callback queue and executes it. This should be called from the main thread. """
        callback = RunOnMainThread.callback_queue.get()
        callback()
