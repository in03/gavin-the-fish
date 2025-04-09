#!/usr/bin/env .venv/bin/python

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Gift Credits
# @raycast.mode fullOutput
# @raycast.packageName ElevenLabs

# Optional parameters:
# @raycast.icon 🎁
# @raycast.argument1 { "type": "text", "placeholder": "Total credits" }

import asyncio
import sys
from playwright.async_api import async_playwright
import subprocess
import time
from datetime import datetime

def show_error(message):
    print(f"Error: {message}", file=sys.stderr)
    subprocess.run(['open', f'raycast://notification?title=Error&message={message}'])
    sys.exit(1)

async def monitor_page_state(page, duration=30):
    """Monitor page state changes over time"""
    print("\n=== Starting Page Monitoring ===")
    print(f"Monitoring for {duration} seconds...")
    
    # Track network requests
    requests = []
    responses = []
    
    def handle_request(request):
        requests.append({
            'time': datetime.now().strftime('%H:%M:%S.%f'),
            'url': request.url,
            'method': request.method,
            'resource_type': request.resource_type
        })
    
    def handle_response(response):
        responses.append({
            'time': datetime.now().strftime('%H:%M:%S.%f'),
            'url': response.url,
            'status': response.status,
            'status_text': response.status_text
        })
    
    # Set up event listeners
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    start_time = time.time()
    last_check = start_time
    
    while time.time() - start_time < duration:
        current_time = time.time()
        if current_time - last_check >= 1:  # Check every second
            print(f"\n=== State at {datetime.now().strftime('%H:%M:%S')} ===")
            
            # Check DOM state
            try:
                # Get all frames
                frames = page.frames
                print(f"\nFrames found: {len(frames)}")
                for i, frame in enumerate(frames):
                    print(f"\nFrame {i}:")
                    print(f"URL: {frame.url}")
                    
                    # Check for buttons
                    buttons = await frame.query_selector_all("button")
                    print(f"Buttons found: {len(buttons)}")
                    for j, button in enumerate(buttons):
                        try:
                            text = await button.text_content()
                            visible = await button.is_visible()
                            print(f"  Button {j}: text='{text}', visible={visible}")
                        except:
                            print(f"  Button {j}: [error reading button]")
                    
                    # Check for specific elements
                    elements = await frame.query_selector_all("#content-subscription, [data-testid='gift-credits-button']")
                    print(f"Special elements found: {len(elements)}")
                    for j, elem in enumerate(elements):
                        try:
                            visible = await elem.is_visible()
                            print(f"  Element {j}: visible={visible}")
                        except:
                            print(f"  Element {j}: [error reading element]")
            
            except Exception as e:
                print(f"Error checking DOM state: {str(e)}")
            
            # Print recent network activity
            if requests:
                print("\nRecent requests:")
                for req in requests[-5:]:
                    print(f"  {req['time']} - {req['method']} {req['url']}")
            
            if responses:
                print("\nRecent responses:")
                for resp in responses[-5:]:
                    print(f"  {resp['time']} - {resp['status']} {resp['url']}")
            
            # Take periodic screenshots
            try:
                timestamp = datetime.now().strftime('%H%M%S')
                await page.screenshot(path=f'/tmp/elevenlabs-monitor-{timestamp}.png')
                print(f"\nScreenshot saved to /tmp/elevenlabs-monitor-{timestamp}.png")
            except Exception as e:
                print(f"Error taking screenshot: {str(e)}")
            
            last_check = current_time
        
        await asyncio.sleep(0.1)  # Small sleep to prevent CPU overload
    
    # Clean up event listeners
    page.remove_listener('request', handle_request)
    page.remove_listener('response', handle_response)
    
    print("\n=== Monitoring Complete ===")
    print(f"Total requests: {len(requests)}")
    print(f"Total responses: {len(responses)}")

async def wait_for_dynamic_content(page, timeout=60000):
    """Wait for dynamic content to load"""
    print("Waiting for dynamic content to load...")
    
    # Wait for the main content to be visible
    await page.wait_for_selector('#content-subscription', state='visible', timeout=timeout)
    
    # Check for iframes
    frames = page.frames
    print(f"Found {len(frames)} frames")
    
    # If we have iframes, try to find the content in them
    if len(frames) > 1:
        print("Checking iframes for content...")
        for i, frame in enumerate(frames[1:], 1):  # Skip the main frame
            try:
                print(f"Checking frame {i}")
                # Wait for content in the iframe
                await frame.wait_for_selector('button', state='visible', timeout=10000)
                print(f"Found visible content in frame {i}")
                return frame
            except Exception as e:
                print(f"Frame {i} check failed: {str(e)}")
                continue
    
    return page

async def find_and_click_by_text(page, text):
    """Find and click an element by its text content"""
    print(f"\nLooking for element with text: {text}")
    
    # Monitor the page state first
    await monitor_page_state(page)
    
    # Try the simplest approach first
    try:
        print("\nTrying direct text selector...")
        # Get all elements with the text
        elements = page.get_by_text(text, exact=False)
        count = await elements.count()
        print(f"Found {count} elements with text '{text}'")
        
        if count > 0:
            # Try to click each element until one works
            for i in range(count):
                try:
                    element = elements.nth(i)
                    print(f"Attempting to click element {i+1}/{count}")
                    await element.click()
                    print("Click successful!")
                    return True
                except Exception as e:
                    print(f"Click failed on element {i+1}: {str(e)}")
                    continue
    except Exception as e:
        print(f"Text selector failed: {str(e)}")
    
    # If that fails, try a more direct approach
    try:
        print("\nTrying direct button search...")
        # Get all buttons and check their text
        buttons = await page.query_selector_all("button")
        print(f"Found {len(buttons)} buttons total")
        
        for i, button in enumerate(buttons):
            button_text = await button.text_content()
            if button_text and text in button_text:
                print(f"Found matching button {i+1}: '{button_text}'")
                await button.click()
                print("Click successful!")
                return True
    except Exception as e:
        print(f"Direct button search failed: {str(e)}")
    
    return False

async def click_gift_credits_directly(page):
    """Directly click the Gift Credits button by its known index"""
    print("\nAttempting to click Gift Credits button directly...")
    
    try:
        # Get all buttons in the main frame
        buttons = await page.query_selector_all("button")
        print(f"Found {len(buttons)} buttons total")
        
        # Try to click button 22 (0-based index 21)
        if len(buttons) > 21:
            print("Clicking button at index 21...")
            await buttons[21].click()
            print("Click successful!")
            return True
        else:
            print(f"Not enough buttons found (need at least 22, found {len(buttons)})")
            return False
    except Exception as e:
        print(f"Error clicking button directly: {str(e)}")
        return False

async def main():
    print("Starting Gift Credits script...")
    
    # Check arguments
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        show_error("Please provide a valid number of credits as an argument")
    
    credits = sys.argv[1]
    print(f"Gifting {credits} credits...")
    
    try:
        async with async_playwright() as p:
            # Connect to existing Chrome instance
            print("Connecting to Chrome...")
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            
            # Get all contexts
            contexts = browser.contexts
            if not contexts:
                show_error("No browser contexts found")
            
            # Find Zendesk tab and get email
            print("Searching for Zendesk tab...")
            user_email = None
            
            for context in contexts:
                pages = context.pages
                for page in pages:
                    url = page.url
                    print(f"Checking tab: {url}")
                    if 'zendesk.com' in url:
                        print("Found Zendesk tab, looking for email element...")
                        try:
                            email_element = await page.wait_for_selector('[data-test-id="email-value-test-id"]', timeout=10000)
                            user_email = await email_element.text_content()
                            user_email = user_email.strip()
                            print(f"Found user email: {user_email}")
                            break
                        except Exception as e:
                            print(f"Error finding email element: {str(e)}")
                
                if user_email:
                    break
            
            if not user_email:
                show_error("Please open a Zendesk ticket first")
            
            # Open ElevenLabs admin directly to user page
            url = f"https://elevenlabs.io/app/th6x-admin/user-info?lookup={user_email}&tab=subscription"
            print(f"Opening ElevenLabs admin: {url}")
            
            # Create a new page in the first context
            page = await contexts[0].new_page()
            
            # Set a longer timeout for navigation
            page.set_default_timeout(60000)
            await page.goto(url, wait_until="domcontentloaded")
            
            # Click Gift Credits
            print("Waiting for Gift Credits button...")
            try:
                # First try the direct approach
                if not await click_gift_credits_directly(page):
                    # Fall back to the text-based search if direct approach fails
                    print("Direct click failed, falling back to text search...")
                    if not await find_and_click_by_text(page, "Gift Credits"):
                        raise Exception("Could not find Gift Credits button")
                
                print("Clicked Gift Credits button")
                
                # Enter credits
                print("Waiting for credits input field...")
                # Wait for the modal to appear
                await page.wait_for_selector('div[role="dialog"]', timeout=10000)
                
                # Find and fill the input field
                input_field = await page.get_by_role("textbox").first
                if not input_field:
                    raise Exception("Credits input field not found")
                
                await input_field.fill(credits)
                print(f"Entered {credits} credits")
                
                # Wait for user action
                print("Please click Continue or Cancel in the dialog...")
                await page.wait_for_selector('div[role="dialog"]', state="hidden", timeout=60000)
                print("Dialog closed successfully")
                
                # Show success notification
                subprocess.run(['open', 'raycast://confetti'])
                subprocess.run(['open', f'raycast://notification?title=Success&message={credits} credits gifted successfully!'])
                
            except Exception as e:
                print(f"Error during interaction: {str(e)}")
                print("Taking screenshot of current page state...")
                await page.screenshot(path='/tmp/elevenlabs-error.png')
                print("Screenshot saved to /tmp/elevenlabs-error.png")
                show_error(f"Failed to complete operation: {str(e)}")
            
            # Keep browser open for user to verify
            print("Script completed. Browser will remain open for verification.")
            print("Press Ctrl+C to close the browser when done.")
            
            try:
                # Keep the script running until user interrupts
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nClosing browser...")
                await browser.close()
    
    except Exception as e:
        print(f"Uncaught error in main function: {str(e)}")
        show_error(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 