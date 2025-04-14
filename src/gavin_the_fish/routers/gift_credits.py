from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import sys
import os
from playwright.async_api import async_playwright
import asyncio
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.panel import Panel

# Initialize Rich console
console = Console()

router = APIRouter(
    prefix="/gift-credits",
    tags=["gift-credits"]
)

class GiftCreditsRequest(BaseModel):
    total_credits: int
    owner: Optional[str] = None
    conversation_id: Optional[str] = None

def show_error(message):
    print(f"Error: {message}", file=sys.stderr)
    raise HTTPException(status_code=500, detail=message)

@router.post("")
async def gift_credits(request: GiftCreditsRequest):
    """Gift credits to a user"""
    try:
        console.print(Panel.fit(
            "[bold green]Starting Gift Credits script...[/bold green]",
            border_style="green"
        ))
        
        # Validate credits
        if request.total_credits <= 0:
            show_error("Please provide a positive number of credits")
        
        credits = str(request.total_credits)
        print(f"Gifting {credits} credits")
        console.print(f"[bold]Gifting {credits} credits...[/bold]")
        
        async with async_playwright() as p:
            # Connect to existing Chrome instance
            print("Connecting to Chrome")
            console.print("[cyan]Connecting to Chrome...[/cyan]")
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            
            # Get all contexts
            contexts = browser.contexts
            if not contexts:
                show_error("No browser contexts found")
            
            # Find Zendesk tab and get email
            print("Searching for Zendesk tab")
            console.print("[cyan]Searching for Zendesk tab...[/cyan]")
            user_email = None
            for context in contexts:
                pages = context.pages
                for page in pages:
                    url = page.url
                    console.print(f"[dim]Checking tab: {url}[/dim]")
                    if 'zendesk.com' in url:
                        print("Found Zendesk tab, looking for email")
                        console.print("[green]Found Zendesk tab, looking for email element...[/green]")
                        try:
                            email_element = await page.wait_for_selector('[data-test-id="email-value-test-id"]', timeout=10000)
                            user_email = await email_element.text_content()
                            user_email = user_email.strip()
                            print(f"Found user email: {user_email}")
                            console.print(f"[bold green]Found user email: {user_email}[/bold green]")
                            break
                        except Exception as e:
                            print(f"Error finding email element: {str(e)}")
                            console.print(f"[yellow]Error finding email element: {str(e)}[/yellow]")
                
                if user_email:
                    break
            
            if not user_email:
                show_error("Please open a Zendesk ticket first")
            
            # Open ElevenLabs admin directly to user page
            url = f"https://elevenlabs.io/app/th6x-admin/user-info?lookup={user_email}&tab=subscription"
            print(f"Opening ElevenLabs admin: {url}")
            console.print(f"[cyan]Opening ElevenLabs admin: {url}[/cyan]")
            
            # Create a new page in the first context
            page = await contexts[0].new_page()
            
            # Set a longer timeout for navigation
            page.set_default_timeout(60000)
            await page.goto(url, wait_until="domcontentloaded")
            
            # Get the main frame (frame 0)
            main_frame = page.frames[0]
            
            # Wait for buttons to be available
            print("Waiting for buttons to load")
            console.print("[cyan]Waiting for buttons to load...[/cyan]")
            try:
                await main_frame.wait_for_function("""
                    () => {
                        const buttons = document.querySelectorAll('button');
                        return buttons.length >= 23;
                    }
                """, timeout=30000)
            except Exception as e:
                print(f"Timeout waiting for buttons: {str(e)}")
                show_error(f"Timed out waiting for buttons to load: {str(e)}")
            
            # Get all buttons in the main frame
            buttons = await main_frame.query_selector_all("button")
            if len(buttons) <= 22:
                show_error(f"Not enough buttons found (need at least 23, found {len(buttons)})")
            
            # Click the Gift Credits button (index 22)
            print("Clicking Gift Credits button")
            console.print("[cyan]Clicking Gift Credits button...[/cyan]")
            await buttons[22].click()
            console.print("[green]Clicked Gift Credits button[/green]")
            
            # Enter credits
            print("Waiting for credits input field")
            console.print("[cyan]Waiting for credits input field...[/cyan]")
            # Wait for the modal to appear and be visible
            modal = await page.wait_for_selector('div[role="dialog"]', state="visible", timeout=10000)
            if not modal:
                show_error("Modal dialog not found")
            
            # Wait for the input field to be visible and enabled
            # Find and fill the input field using aria-label
            input_field = await modal.query_selector('input[aria-label="The number of credits to gift to the workspace"]')
            if not input_field:
                show_error("Credits input field not found in modal")
            
            # Try to focus and click the input field first
            await input_field.click()
            await input_field.fill(credits)
            print(f"Entered {credits} credits")
            console.print(f"[bold green]Entered {credits} credits[/bold green]")
            
            return {
                "status": "success",
                "message": f"Successfully gifted {credits} credits to {user_email}",
                "user_email": user_email
            }
    
    except Exception as e:
        print(f"Uncaught error in main function: {str(e)}")
        console.print(f"[bold red]Uncaught error in main function:[/bold red] {str(e)}")
        show_error(f"Error: {str(e)}")
    finally:
        if 'page' in locals():
            await page.close()
        if 'browser' in locals():
            await browser.close() 