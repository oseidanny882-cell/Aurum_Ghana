import pathlib

p = pathlib.Path("c:/Users/Codewithme/jewelry-gh/frontend/styles.css")
t = p.read_text(encoding="utf-8")

css = """
/* Search Modal */
.search-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 10vh;
    z-index: 1000;
    backdrop-filter: blur(4px);
    animation: fadeIn 0.2s ease;
}
.search-overlay[hidden] { display: none; }
.search-overlay.is-open { display: flex; }
.search-modal {
    background: var(--color-surface, #fff);
    border-radius: 8px;
    width: 90%;
    max-width: 600px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
    padding: 1.5rem;
    animation: slideDown 0.2s ease;
}
.search-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
}
.search-modal-header h2 {
    margin: 0;
    font-family: "Cormorant Garamond", serif;
    font-size: 1.5rem;
    font-weight: 500;
}
.search-form {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    border: 1px solid var(--color-border, #e5e5e5);
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    background: #fff;
    transition: border-color 0.15s ease;
}
.search-form:focus-within {
    border-color: var(--color-primary, #b8860b);
}
.search-form input {
    flex: 1;
    border: none;
    outline: none;
    font-size: 1rem;
    background: transparent;
    font-family: inherit;
    color: var(--color-text, #1a1a1a);
    padding: 0.25rem 0;
}
.search-form input::placeholder {
    color: var(--color-text-muted, #999);
}
.search-submit-btn {
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    color: var(--color-text, #1a1a1a);
    display: flex;
    align-items: center;
    justify-content: center;
}
.search-submit-btn:hover { color: var(--color-primary, #b8860b); }
.search-close-btn {
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    color: var(--color-text, #1a1a1a);
    display: flex;
    align-items: center;
    justify-content: center;
}
.search-hint {
    margin: 0.75rem 0 0;
    font-size: 0.8rem;
    color: var(--color-text-muted, #999);
    text-align: center;
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes slideDown {
    from { transform: translateY(-20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}
"""

# Only add if not already there
if "Search Modal" not in t:
    t = t + css
    p.write_text(t, encoding="utf-8")
    print("SUCCESS: Added search modal CSS")
else:
    print("Already has Search Modal CSS")
