from playwright.sync_api import sync_playwright
import config

def get_current_dom():
    with sync_playwright().start() as p:
        browser = p.chromium.connect_over_cdp(config.CHROME_URL)
        context = browser.contexts[0]
        page = context.pages[0]

        js_script = f"""
        () => {{
            const menus = document.querySelectorAll('.dropdown, .menu, [aria-haspopup="true"]');
            menus.forEach(m => {{ m.style.display = 'block'; }});

            const selector = `
                button, a, input, select, textarea, nav, 
                [role="navigation"], [role="menuitem"], [role="button"], [role="link"], [role="combobox"], 
                [onclick], [tabindex="0"], [aria-haspopup="true"], [aria-expanded], 
                .nav-link, .menu-item, .dropdown-item
            `;
            
            const interactables = document.querySelectorAll(selector);
            
            return Array.from(interactables).map((el, index) => {{
                el.setAttribute('{config.AI_ATTRIBUTE}', index);
                
                const cleanText = el.innerText.trim() || 
                                el.getAttribute('aria-label') || 
                                el.placeholder || 
                                el.title || 
                                (el.tagName === 'INPUT' ? el.value : "");

                return {{
                    id: index,
                    tag: el.tagName,
                    text: cleanText || "no text",
                    role: el.getAttribute('role') || "none",
                    isHidden: el.offsetParent === null || window.getComputedStyle(el).visibility === 'hidden',
                    isNav: el.closest('nav') !== null || el.getAttribute('role') === 'navigation',
                    rect: el.getBoundingClientRect() 
                }};
            }}).filter(item => !item.isHidden && item.text !== "no text");
        }}
        """
        dom_json = page.evaluate(js_script)
        return dom_json