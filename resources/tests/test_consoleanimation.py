#  Copyright (c) $YEAR$. Copyright (c) $YEAR$ Wrench.AI., Willem van der Schans, Jeong Kim
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#

import unittest
import time

from Utility import ConsoleAnimation


class TestConsoleAnimation(unittest.TestCase):
    def test_loading_bar_animation_5_seconds(self):
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

    def test_blink_animation_5_seconds(self):
        total_duration = 2  # Total duration in seconds
        update_interval = 0.5  # How often to update the progress (in seconds)
        total_updates = int(total_duration / update_interval)  # Calculate how many times to update based on interval

        animation = ConsoleAnimation(animation_type="blink", total_length=total_updates, show_timer=True, flush = False)
        animation.start()

        for _ in range(total_updates):
            time.sleep(update_interval)  # Simulate work by sleeping
            animation.update_progress()  # Update the progress of the animation

        animation.stop()

        # This is a visual test, so there's no assert statement. The success criteria are based on the visual output.
        print("\nTest completed. The loading bar should have progressed over approximately 5 seconds.")

if __name__ == '__main__':
    unittest.main()
