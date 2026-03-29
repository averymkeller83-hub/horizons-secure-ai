"""HTML contact capture form endpoint.

Serves a standalone HTML form that customers or website visitors
can use to request a repair quote. Submits to the /api/v1/leads/capture
endpoint.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from config.settings import settings

router = APIRouter(tags=["forms"])

FORM_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Get a Repair Quote - {business_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .form-container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 480px;
            width: 100%;
        }}
        h1 {{
            font-size: 1.5rem;
            margin-bottom: 8px;
            color: #1a1a1a;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 24px;
            font-size: 0.95rem;
        }}
        label {{
            display: block;
            font-weight: 600;
            margin-bottom: 4px;
            font-size: 0.9rem;
        }}
        input, select, textarea {{
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
            margin-bottom: 16px;
            transition: border-color 0.2s;
        }}
        input:focus, select:focus, textarea:focus {{
            outline: none;
            border-color: #2563eb;
        }}
        textarea {{ resize: vertical; min-height: 100px; }}
        button {{
            width: 100%;
            padding: 12px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }}
        button:hover {{ background: #1d4ed8; }}
        .success {{
            background: #ecfdf5;
            color: #065f46;
            padding: 16px;
            border-radius: 8px;
            margin-top: 16px;
            display: none;
        }}
        .error {{
            background: #fef2f2;
            color: #991b1b;
            padding: 16px;
            border-radius: 8px;
            margin-top: 16px;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="form-container">
        <h1>Get a Free Repair Quote</h1>
        <p class="subtitle">Tell us about your device and we'll get back to you quickly.</p>
        <form id="captureForm">
            <label for="name">Your Name *</label>
            <input type="text" id="name" name="name" required>

            <label for="email">Email</label>
            <input type="email" id="email" name="email" placeholder="you@example.com">

            <label for="phone">Phone</label>
            <input type="tel" id="phone" name="phone" placeholder="(555) 123-4567">

            <label for="device_type">Device Type</label>
            <select id="device_type" name="device_type">
                <option value="">Select a device...</option>
                <option value="iPhone">iPhone</option>
                <option value="Samsung Phone">Samsung Phone</option>
                <option value="Other Phone">Other Phone</option>
                <option value="iPad">iPad</option>
                <option value="Other Tablet">Other Tablet</option>
                <option value="MacBook">MacBook</option>
                <option value="Laptop">Laptop (PC)</option>
                <option value="Desktop">Desktop</option>
                <option value="Game Console">Game Console</option>
                <option value="Other">Other</option>
            </select>

            <label for="issue_description">What's the issue? *</label>
            <textarea id="issue_description" name="issue_description" required
                placeholder="Describe the problem with your device..."></textarea>

            <button type="submit">Request Quote</button>
        </form>
        <div class="success" id="successMsg">
            Thank you! We've received your request and will get back to you shortly.
        </div>
        <div class="error" id="errorMsg"></div>
    </div>

    <script>
        document.getElementById('captureForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const form = e.target;
            const data = {{
                name: form.name.value,
                email: form.email.value || null,
                phone: form.phone.value || null,
                device_type: form.device_type.value || null,
                issue_description: form.issue_description.value,
            }};

            try {{
                const resp = await fetch('/api/v1/leads/capture', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(data),
                }});

                if (resp.ok) {{
                    form.style.display = 'none';
                    document.getElementById('successMsg').style.display = 'block';
                }} else {{
                    const err = await resp.json();
                    const errDiv = document.getElementById('errorMsg');
                    errDiv.textContent = err.detail || 'Something went wrong. Please try again.';
                    errDiv.style.display = 'block';
                }}
            }} catch (err) {{
                const errDiv = document.getElementById('errorMsg');
                errDiv.textContent = 'Network error. Please check your connection and try again.';
                errDiv.style.display = 'block';
            }}
        }});
    </script>
</body>
</html>"""


@router.get("/quote", response_class=HTMLResponse)
async def contact_form():
    """Serve the contact capture form."""
    return FORM_HTML.format(business_name=settings.business_name)
