import argparse
import sys
from pathlib import Path
from smart_qa.client import LLMClient
from smart_qa.custom_exceptions import LLMAPIError


def load_text_from_file(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def save_to_file(filepath: str, content: str):
    path = Path(filepath)
    path.write_text(content, encoding="utf-8")
    print(f"✓ Saved to {filepath}")


def interactive_mode(client: LLMClient, args):
    if args.file:
        text = load_text_from_file(args.file)
        print(f"✓ Loaded text from {args.file} ({len(text)} characters)\n")
    else:
        print("Enter/paste your text (press Ctrl+D on Unix or Ctrl+Z on Windows when done):")
        text = sys.stdin.read().strip()
        if not text:
            print("Error: No text provided")
            return
    
    print("\nChoose an action:")
    print("1. Summarize")
    print("2. Ask a question")
    print("3. Extract entities")
    choice = input("\nEnter choice (1-3): ").strip()
    
    try:
        if choice == "1":
            result = client.summarize(text)
            print("\n=== SUMMARY ===")
            print(result)
            
        elif choice == "2":
            question = input("\nEnter your question: ").strip()
            result = client.ask(text, question)
            print("\n=== ANSWER ===")
            print(result)
            
        elif choice == "3":
            result = client.extract_entities(text)
            print("\n=== ENTITIES ===")
            print(f"People: {result.get('People', [])}")
            print(f"Dates: {result.get('Dates', [])}")
            print(f"Locations: {result.get('Locations', [])}")
            result = str(result)
            
        else:
            print("Invalid choice")
            return
        
        if args.save:
            save_to_file(args.save, result)
            
    except LLMAPIError as e:
        print(f"\n✗ API Error: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Smart Q&A Tool - AI-powered text analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="Load text from a file instead of stdin"
    )
    
    parser.add_argument(
        "--save",
        type=str,
        help="Save the output to a file"
    )
    
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the local cache before running"
    )
    
    args = parser.parse_args()
    
    if args.clear_cache:
        LLMClient.clear_cache()
        print("✓ Cache cleared")
        if not args.file:
            return
    
    try:
        client = LLMClient()
        interactive_mode(client, args)
        
    except LLMAPIError as e:
        print(f"✗ Client Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()