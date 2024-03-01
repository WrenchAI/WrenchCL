import os
import threading
import sys
import time
from numbers import Number

try:
    from colorama import Fore, Style

    colorama_imported = True
except ImportError:
    colorama_imported = False


class ConsoleAnimation(threading.Thread):
    """
    A class for creating and controlling console-based animations, such as a blinking dot or a loading bar, with
    optional progress tracking features like elapsed time, iterations per second (IPS), and estimated remaining time.
    The class leverages threading to run the animation in the background, allowing concurrent tasks without blocking
    execution. It supports color-coded progress indication when 'colorama' is available, enhancing visual feedback.

    This class is designed to be flexible and can be used in various environments, including AWS Lambda. By default,
    it detects if it's running in an AWS Lambda environment and adjusts its behavior accordingly to avoid issues
    with threading and output in such constrained environments.

    Attributes:
        animation_type (str): The type of animation ('Bar' or another string for blinking dot by default).
        task (str): A brief description of the task associated with the animation. Defaults to 'Processing' if not provided.
        total_length (int | float | None): The total number of updates expected for the animation. Essential for calculating
            progress in the loading bar animation. If not provided or invalid, defaults to a blinking dot animation.
        show_timer (bool): If True, display elapsed time, IPS, and estimated remaining time alongside the animation.
        flush (bool): If True, clears the animation from the console upon stopping. Applicable to both types of animations.

    Methods:
        overwrite_lambda_mode(setting: bool): Allows manually overriding the detection of AWS Lambda environment to enable
            or disable specific behaviors intended for Lambda execution contexts. This is particularly useful when you want to
            force the animation to behave as it would outside of Lambda, or vice versa. By default, the class will attempt to
            detect if it's running in Lambda and disable certain features that are not compatible with Lambda's execution model,
            such as threading and real-time console updates.

        update_progress(): Increments the current progress by one. It redraws the loading bar with updated progress,
            recalculates and displays new statistics. Applicable only for the loading bar animation type.

        stop(): Stops the animation, optionally clears the console line (based on the animation type and `flush` attribute),
            and prints a completion message if the loading bar animation is used without flushing.

    Usage Example:
        # Setting up a 5-second task with updates every 0.5 seconds
            total_duration = 5
            update_interval = 0.5
            total_updates = int(total_duration / update_interval)

        # Initializing and starting the animation
            animation = ConsoleAnimation(animation_type="bar", total_length=total_updates, show_timer=True)
            animation.start()

        # Simulating task progress
            for _ in range(total_updates):
                time.sleep(update_interval)
                animation.update_progress()

        # Stopping the animation upon task completion
            animation.stop()

        # Output will include a color-coded loading bar with progress percentage and stats on elapsed time, IPS,
        # and remaining time. The color of the bar and percentage changes based on the progress.

    Note:
        This class requires the 'colorama' module for colored output. If 'colorama' is not installed, the output will
        not be color-coded. Ensure 'colorama' is installed and available in your environment to utilize color features.
        The behavior of this class can be adjusted for AWS Lambda execution environments using the `overwrite_lambda_mode` method.
    """

    def __init__(self, animation_type=None, task: str = None, total_length=None, show_timer: bool = False,
                 flush: bool = False):
        super().__init__()
        animation_type = animation_type.lower() if isinstance(animation_type, str) else animation_type
        # First, validate total_length without changing animation_type
        valid_total_length = self._validate_and_set_total_length(total_length)

        # Set animation_type based on the input and validity of total_length
        if (animation_type == 'bar' or animation_type == 2) and valid_total_length is not None:
            self.animation_type = 2  # Loading bar
        else:
            self.animation_type = 1  # Blinking dot, default if total_length is None or invalid, or another animation type is specified

        self.total_length = valid_total_length
        self.flush = flush
        self.current_progress = 0
        self._stop_event = threading.Event()
        self.daemon = True
        self.show_timer = show_timer
        self.start_time = None
        self.task = task.title() if isinstance(task, str) else "Processing"
        self.running_on_lambda = 'AWS_LAMBDA_FUNCTION_NAME' in os.environ
        self.elapsed_time = 0
    def overwrite_lambda_mode(self, setting: bool) -> None:
        self.running_on_lambda = setting

    def _validate_and_set_total_length(self, total_length):
        if isinstance(total_length, (str, Number)):
            try:
                return max(int(total_length), 0)  # Ensure non-negative
            except ValueError:
                pass  # Handle non-integer string gracefully
        elif isinstance(total_length, float):  # Directly support float without conversion
            return max(total_length, 0.0)  # Ensure non-negative
        # If total_length is none or invalid, revert to BLINKING_DOT
        self.animation_type = 1
        return None

    def run(self):
        if not self.running_on_lambda:
            self.start_time = time.time()  # Start time of the animation
            if self.animation_type == 1:
                self._run_blinking_dot()
            elif self.animation_type == 2:
                self._run_loading_bar()
        else:
            pass

    @staticmethod
    def _format_time(seconds):
        """Format time in seconds to hours:minutes:seconds."""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

    def _draw_loading_bar(self):
        bar_length = 20
        percent = (self.current_progress / self.total_length) * 100 if self.total_length else 0
        bar_fill = int(percent / (100 / bar_length))
        self.elapsed_time = time.time() - self.start_time
        ips = self.current_progress / self.elapsed_time if self.elapsed_time > 0 else 0
        estimated_total_time = self.elapsed_time / (
                self.current_progress / self.total_length) if self.current_progress else 0
        estimated_remaining_time = estimated_total_time - self.elapsed_time
        formatted_remaining_time = self._format_time(estimated_remaining_time)

        # Color the percentage based on its value
        if colorama_imported:
            if percent < 25:
                percent_color = Fore.LIGHTRED_EX
            elif percent < 50:
                percent_color = Fore.LIGHTMAGENTA_EX
            elif percent < 75:
                percent_color = Fore.LIGHTYELLOW_EX
            elif percent < 95:
                percent_color = Fore.LIGHTBLUE_EX
            else:
                percent_color = Fore.LIGHTGREEN_EX
        else:
            percent_color = ''  # No color if colorama is not available

        # Apply color to the bar if colorama is available
        if colorama_imported:
            bar = f'{Fore.LIGHTWHITE_EX}[{percent_color}{"=" * bar_fill}{Fore.LIGHTBLACK_EX}{" " * (bar_length - bar_fill)}{Fore.LIGHTWHITE_EX}]{Style.RESET_ALL}'
        else:
            bar = '[' + '=' * bar_fill + ' ' * (bar_length - bar_fill) + ']'

        timer_and_ips_info = ''
        if self.show_timer:
            timer_and_ips_info = f'Stats: {Fore.LIGHTBLACK_EX}Elapsed:{Style.RESET_ALL} {self._format_time(self.elapsed_time)}{Fore.LIGHTBLACK_EX}, OpS: {Style.RESET_ALL}{ips:.2f}{Fore.LIGHTBLACK_EX}, Remaining: {Style.RESET_ALL}{formatted_remaining_time}'

        sys.stdout.write(
            f'\r{self.task} : {bar} {percent_color}{percent:.2f}%{Style.RESET_ALL} Complete | {timer_and_ips_info}')
        sys.stdout.flush()

    def _run_blinking_dot(self):
        dot_state = 0
        while not self._stop_event.is_set():
            self.elapsed_time = time.time() - self.start_time
            dots = '.' * (dot_state % 3 + 1)  # Cycle through 1 to 3 dots.

            if colorama_imported:
                sys.stdout.write(f"\r{Fore.CYAN}[{self.elapsed_time:.2f}s]{Style.RESET_ALL} {self.task} {Style.RESET_ALL}" + dots)
            else:
                sys.stdout.write(f"\r[{self.elapsed_time:.2f}s] {self.task}" + dots)

            sys.stdout.flush()
            time.sleep(0.5)
            dot_state += 1

        # Clear the line after stopping
        sys.stdout.write("\r" + " " * (len(self.task) + 20))  # Clear with spaces
        sys.stdout.write("\r")  # Return the cursor to the start of the line
        sys.stdout.flush()

    def _run_loading_bar(self):
        while not self._stop_event.is_set() and self.current_progress <= self.total_length:
            self._draw_loading_bar()
            time.sleep(0.2)  # Adjust based on actual progress updates rather than fixed sleep

    def update_progress(self):
        if self.total_length and self.animation_type != 1:
            self.current_progress += 1
            self._draw_loading_bar()

    def stop(self):
        self._stop_event.set()
        self.join()  # Wait for thread to finish

        # If it's a blinking dot animation, clear the line to clean up.
        if self.animation_type == 1:
            if self.flush:
                sys.stdout.write('\r' + ' ' * 60 + '\r')  # Clear the line
                sys.stdout.flush()
            if colorama_imported:
                sys.stdout.write(f"{Fore.CYAN}[{self.elapsed_time:.2f}s] {Style.RESET_ALL}{self.task} : {Fore.LIGHTGREEN_EX}completed{Style.RESET_ALL}")
            else:
                sys.stdout.write(f"[{self.elapsed_time:.2f}s] {self.task} : Completed")
        if self.animation_type == 2:
            if colorama_imported:
                sys.stdout.write(f"\n{Fore.CYAN}[{self.elapsed_time:.2f}s] {Style.RESET_ALL}{self.task} : {Fore.LIGHTGREEN_EX}completed{Style.RESET_ALL}")
            else:
                sys.stdout.write(f"\n[{self.elapsed_time:.2f}s] {self.task} : Completed")


if __name__ == "__main__":
    total_duration = 2  # Total duration in seconds
    update_interval = 0.5  # How often to update the progress (in seconds)
    total_updates = int(total_duration / update_interval)  # Calculate how many times to update based on interval

    animation = ConsoleAnimation(animation_type="bar", total_length=total_updates, show_timer=True)
    animation.start()

    for _ in range(total_updates):
        time.sleep(update_interval)  # Simulate work by sleeping
        animation.update_progress()  # Update the progress of the animation

    animation.stop()

    # This is a visual test, so there's no assert statement. The success criteria are based on the visual output.
    print("\nTest completed. The loading bar should have progressed over approximately 5 seconds.")

    total_duration = 2  # Total duration in seconds
    update_interval = 0.5  # How often to update the progress (in seconds)
    total_updates = int(total_duration / update_interval)  # Calculate how many times to update based on interval

    animation = ConsoleAnimation(animation_type="blink", total_length=total_updates, show_timer=True, flush = False)
    animation.start()

    for _ in range(total_updates):
        time.sleep(update_interval)  # Simulate work by sleeping
        animation.update_progress()  # Update the progress of the animation

    animation.stop()
