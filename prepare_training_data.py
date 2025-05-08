# prepare_training_data.py
import pandas as pd
from db_connector import get_pos_data
import yaml
import os
import re
import sys
from typing import Optional

def clean_text(text: Optional[str]) -> Optional[str]:
    """Remove non-printable characters and zero-width spaces from text."""
    if not isinstance(text, str):
        return None
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e\u2060-\u206f]', '', text)
    return text.strip()

def generate_nlu_data():
    """Generate NLU training data from POS database."""
    try:
        pos_data = get_pos_data()
        if pos_data is None or pos_data.empty:
            print("Error: Failed to fetch POS data. Check database connection.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: Unable to connect to database: {str(e)}")
        sys.exit(1)

    nlu_data = {
        "version": "3.1",
        "nlu": [
            {
                "intent": "greet",
                "examples": [
                    "Hi!",
                    "Hello there",
                    "Hey, what's up?",
                    "Good day!",
                    "Can you assist me?",
                    "Yo, how's it going?"
                ]
            },
            {
                "intent": "ask_price",
                "examples": []
            },
            {
                "intent": "ask_inventory",
                "examples": []
            },
            {
                "intent": "process_return",
                "examples": [
                    "I'd like to return an item",
                    "Can you help with a return?",
                    "How do I return something?",
                    "Need to return a purchase",
                    "Process a return for me",
                    "I want to send this back"
                ]
            },
            {
                "intent": "ask_discount",
                "examples": []
            },
            {
                "intent": "check_invoice",
                "examples": []
            },
            {
                "intent": "affirm",
                "examples": [
                    "Yes",
                    "Absolutely",
                    "Yup",
                    "That's correct",
                    "Sure thing",
                    "Yeah",
                    "[INV123](transaction_id)",
                    "[TXN456](transaction_id)",
                    "[INV789](invoice_number)",
                    "[INV001](invoice_number)"
                ]
            },
            {
                "intent": "deny",
                "examples": [
                    "No",
                    "Nope",
                    "Not at all",
                    "I don't think so",
                    "No thanks",
                    "Nah"
                ]
            }
        ]
    }

    for item in pos_data["ITEM_DESCRIPTION"].unique():
        cleaned_item = clean_text(item)
        if not cleaned_item:
            continue

        # Extract color variant if present (e.g., "(Sky Blue+Black)")
        color_match = re.search(r'\((.*?)\)', cleaned_item)
        product_name = re.sub(r'\s*\(.*?\)', '', cleaned_item).strip()
        color = color_match.group(1) if color_match else "Unknown"

        # Generate ask_price examples with proper entity annotations
        nlu_data["nlu"][1]["examples"].extend([
            f"How much is [{product_name}](product) [({color})](color)?",
            f"What's the price of [{product_name}](product) [({color})](color)?",
            f"Price of [{product_name}](product) [({color})](color)?",
            f"How much does [{product_name}](product) [({color})](color) cost?",
            f"Can you tell me the price of [{product_name}](product) [({color})](color)?",
            f"How much for [{product_name}](product) in [({color})](color)?",
            f"What's the cost of [{product_name}](product) [({color})](color)?",
            f"Price for [{product_name}](product) [({color})](color)?",
            f"How much is {product_name}?",  # Partial name examples
            f"Price of {product_name.split()[0]}?"  # First word of product name
        ])

        # Generate ask_inventory examples with proper entity annotations
        nlu_data["nlu"][2]["examples"].extend([
            f"Is [{product_name}](product) [({color})](color) in stock?",
            f"Do you have [{product_name}](product) [({color})](color)?",
            f"Stock of [{product_name}](product) [({color})](color)?",
            f"Availability of [{product_name}](product) [({color})](color)?",
            f"Can you check if [{product_name}](product) [({color})](color) is available?",
            f"Is [{product_name}](product) [({color})](color) available?",
            f"Do you have any [{product_name}](product) [({color})](color) in stock?",
            f"Is {product_name} in stock?",  # Partial name examples
            f"Do you have {product_name.split()[0]}?"  # First word of product name
        ])

        # Generate ask_discount examples
        nlu_data["nlu"][4]["examples"].extend([
            f"Any discounts on [{product_name}](product) [({color})](color)?",
            f"Is there a deal available for [{product_name}](product) [({color})](color)?",
            f"Can you offer a discount on [{product_name}](product) [({color})](color)?",
            f"What promotions are running for [{product_name}](product) [({color})](color)?",
            f"Discount on [{product_name}](product) [({color})](color)?",
            f"Are there any sales on [{product_name}](product) [({color})](color)?",
            f"Any deals on {product_name}?",  # Partial name examples
            f"Discount for {product_name.split()[0]}?"  # First word of product name
        ])

    # Generate check_invoice examples
    sample_invoices = pos_data["INVOICE_NO"].unique()[:10].tolist() if not pos_data["INVOICE_NO"].empty else ["INV123", "INV456"]
    for invoice in sample_invoices:
        nlu_data["nlu"][5]["examples"].extend([
            f"What items are in invoice [{invoice}](invoice_number)?",
            f"Can you show me the items for [{invoice}](invoice_number)?",
            f"Details for invoice [{invoice}](invoice_number)?",
            f"What's in [{invoice}](invoice_number)?",
            f"Check invoice [{invoice}](invoice_number)",
            f"Items for [{invoice}](invoice_number)"
        ])

    # Format examples as YAML-compatible strings
    for intent in nlu_data["nlu"]:
        if "examples" in intent:
            intent["examples"] = "\n".join([f"- {ex}" for ex in intent["examples"]])

    # Write to nlu.yml
    os.makedirs("data", exist_ok=True)
    nlu_file = "data/nlu.yml"
    try:
        with open(nlu_file, "w", encoding="utf-8") as f:
            yaml.dump(nlu_data, f, allow_unicode=True, sort_keys=False)
        print(f"NLU data generated successfully at {nlu_file}")
    except Exception as e:
        print(f"Error: Failed to write to {nlu_file}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    generate_nlu_data()