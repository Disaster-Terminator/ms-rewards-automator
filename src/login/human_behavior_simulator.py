"""
Human Behavior Simulator for Login.

This module simulates human-like behavior to bypass automation detection:
- Natural mouse movements with Bezier curves
- Variable typing speed with realistic delays
- Random pauses and micro-movements
- Natural interaction patterns
"""

import asyncio
import logging
import math
import random
from typing import Any


class HumanBehaviorSimulator:
    """
    Simulates human-like behavior for browser automation.

    This class provides methods to interact with web pages in a way
    that mimics real human behavior, making it harder for anti-bot
    systems to detect automation.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the human behavior simulator.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Typing speed parameters (milliseconds per character)
        self.typing_speed_min = 80  # Fast typing
        self.typing_speed_max = 200  # Slow typing
        self.typing_speed_avg = 120  # Average typing

        # Pause probabilities and durations
        self.pause_probability = 0.15  # 15% chance of pause between chars
        self.pause_duration_min = 100
        self.pause_duration_max = 500

        # Mouse movement parameters
        self.mouse_speed = 1.0  # Multiplier for movement speed

    async def human_type(self, page: Any, selector: str, text: str, timeout: int = 10000) -> bool:
        """
        Type text with human-like behavior.

        This method:
        1. Moves mouse to the input field
        2. Clicks to focus
        3. Types with variable speed and random pauses
        4. Triggers proper input events

        Args:
            page: Playwright page object
            selector: CSS selector for input field
            text: Text to type
            timeout: Timeout in milliseconds

        Returns:
            True if successful, False otherwise
        """
        try:
            # Wait for element to be visible
            await page.wait_for_selector(selector, state="visible", timeout=timeout)

            # Get element bounding box for mouse movement
            element = await page.query_selector(selector)
            if not element:
                self.logger.error(f"Element not found: {selector}")
                return False

            box = await element.bounding_box()
            if not box:
                self.logger.error(f"Could not get bounding box for: {selector}")
                return False

            # Move mouse to element with natural movement
            target_x = box["x"] + box["width"] / 2
            target_y = box["y"] + box["height"] / 2
            await self.move_mouse_naturally(page, target_x, target_y)

            # Small delay before click (human reaction time)
            await asyncio.sleep(random.uniform(0.1, 0.3))

            # Click to focus
            await page.mouse.click(target_x, target_y)
            await asyncio.sleep(random.uniform(0.05, 0.15))

            # Clear existing content first
            await page.evaluate(
                """(selector) => {
                const element = document.querySelector(selector);
                if (element) element.value = "";
            }""",
                selector,
            )

            # Type each character with human-like timing
            for i, char in enumerate(text):
                # Type the character using keyboard.type (more natural than fill)
                await page.keyboard.type(char)

                # Variable delay between characters
                if i < len(text) - 1:  # Don't delay after last character
                    delay = self.get_typing_delay()
                    await asyncio.sleep(delay / 1000.0)

                    # Random pause (simulating thinking or checking)
                    if random.random() < self.pause_probability:
                        pause = (
                            random.uniform(self.pause_duration_min, self.pause_duration_max)
                            / 1000.0
                        )
                        await asyncio.sleep(pause)

            # Trigger input and change events to ensure form validation
            await page.evaluate(
                """(selector) => {
                const element = document.querySelector(selector);
                if (element) {
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }""",
                selector,
            )

            self.logger.debug(f"Human-typed text into: {selector}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to human-type into {selector}: {e}")
            return False

    async def human_click(self, page: Any, selector: str, timeout: int = 10000) -> bool:
        """
        Click an element with human-like behavior.

        This method:
        1. Moves mouse naturally to the element
        2. Adds small random offset (humans don't click exact center)
        3. Pauses briefly before clicking
        4. Performs the click

        Args:
            page: Playwright page object
            selector: CSS selector for element
            timeout: Timeout in milliseconds

        Returns:
            True if successful, False otherwise
        """
        try:
            # Wait for element to be visible and enabled
            await page.wait_for_selector(selector, state="visible", timeout=timeout)

            # Get element bounding box
            element = await page.query_selector(selector)
            if not element:
                self.logger.error(f"Element not found: {selector}")
                return False

            box = await element.bounding_box()
            if not box:
                self.logger.error(f"Could not get bounding box for: {selector}")
                return False

            # Calculate click position with small random offset
            # (humans don't click exact center)
            center_x = box["x"] + box["width"] / 2
            center_y = box["y"] + box["height"] / 2

            # Add random offset (within 30% of element size)
            offset_x = random.uniform(-box["width"] * 0.3, box["width"] * 0.3)
            offset_y = random.uniform(-box["height"] * 0.3, box["height"] * 0.3)

            target_x = center_x + offset_x
            target_y = center_y + offset_y

            # Move mouse naturally to target
            await self.move_mouse_naturally(page, target_x, target_y)

            # Human reaction time before click
            await asyncio.sleep(random.uniform(0.1, 0.3))

            # Perform click
            await page.mouse.click(target_x, target_y)

            # Small delay after click (human doesn't instantly move away)
            await asyncio.sleep(random.uniform(0.05, 0.15))

            self.logger.debug(f"Human-clicked element: {selector}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to human-click {selector}: {e}")
            return False

    async def move_mouse_naturally(
        self, page: Any, target_x: float, target_y: float, steps: int | None = None
    ) -> None:
        """
        Move mouse to target position with natural Bezier curve movement.

        Args:
            page: Playwright page object
            target_x: Target X coordinate
            target_y: Target Y coordinate
            steps: Number of steps (auto-calculated if None)
        """
        try:
            # Get current mouse position (or start from random position)
            # Note: Playwright doesn't expose current mouse position,
            # so we'll start from a random position near the viewport
            viewport = page.viewport_size
            start_x = random.uniform(viewport["width"] * 0.3, viewport["width"] * 0.7)
            start_y = random.uniform(viewport["height"] * 0.3, viewport["height"] * 0.7)

            # Calculate distance and determine number of steps
            distance = math.sqrt((target_x - start_x) ** 2 + (target_y - start_y) ** 2)
            if steps is None:
                steps = max(10, int(distance / 10))  # More steps for longer distances

            # Generate Bezier curve control points
            # Add some randomness to make movement less predictable
            control1_x = start_x + (target_x - start_x) * random.uniform(0.2, 0.4)
            control1_y = start_y + (target_y - start_y) * random.uniform(0.2, 0.4)
            control1_y += random.uniform(-50, 50)  # Add vertical variation

            control2_x = start_x + (target_x - start_x) * random.uniform(0.6, 0.8)
            control2_y = start_y + (target_y - start_y) * random.uniform(0.6, 0.8)
            control2_y += random.uniform(-50, 50)  # Add vertical variation

            # Move along Bezier curve
            for i in range(steps + 1):
                t = i / steps

                # Cubic Bezier curve formula
                x = (
                    (1 - t) ** 3 * start_x
                    + 3 * (1 - t) ** 2 * t * control1_x
                    + 3 * (1 - t) * t**2 * control2_x
                    + t**3 * target_x
                )
                y = (
                    (1 - t) ** 3 * start_y
                    + 3 * (1 - t) ** 2 * t * control1_y
                    + 3 * (1 - t) * t**2 * control2_y
                    + t**3 * target_y
                )

                await page.mouse.move(x, y)

                # Variable delay between movements (faster in middle, slower at ends)
                if i < steps:
                    # Ease-in-out timing
                    progress = i / steps
                    if progress < 0.5:
                        speed_factor = 2 * progress * progress
                    else:
                        speed_factor = 1 - 2 * (1 - progress) * (1 - progress)

                    delay = (5 + random.uniform(-2, 2)) * (1 - speed_factor * 0.5)
                    await asyncio.sleep(delay / 1000.0)

        except Exception as e:
            self.logger.debug(f"Mouse movement error (non-critical): {e}")
            # Fallback to direct movement
            await page.mouse.move(target_x, target_y)

    def get_typing_delay(self) -> float:
        """
        Get a realistic typing delay in milliseconds.

        Uses a normal distribution centered around average typing speed
        with occasional longer delays (simulating thinking).

        Returns:
            Delay in milliseconds
        """
        # 90% of the time: normal typing speed
        if random.random() < 0.9:
            # Normal distribution around average speed
            delay = random.gauss(self.typing_speed_avg, 30)
            # Clamp to min/max range
            delay = max(self.typing_speed_min, min(self.typing_speed_max, delay))
        else:
            # 10% of the time: longer delay (thinking/checking)
            delay = random.uniform(300, 800)

        return delay

    async def random_mouse_movement(self, page: Any) -> None:
        """
        Perform a small random mouse movement.

        This simulates natural micro-movements that humans make
        while reading or thinking.

        Args:
            page: Playwright page object
        """
        try:
            viewport = page.viewport_size
            x = random.uniform(viewport["width"] * 0.3, viewport["width"] * 0.7)
            y = random.uniform(viewport["height"] * 0.3, viewport["height"] * 0.7)

            await self.move_mouse_naturally(page, x, y, steps=5)
        except Exception as e:
            self.logger.debug(f"Random mouse movement error (non-critical): {e}")

    async def human_delay(self, min_ms: float = 500, max_ms: float = 2000) -> None:
        """
        Add a human-like delay.

        Args:
            min_ms: Minimum delay in milliseconds
            max_ms: Maximum delay in milliseconds
        """
        delay = random.uniform(min_ms, max_ms) / 1000.0
        await asyncio.sleep(delay)
