import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from nlp.pipeline import nlp_pipeline
except ImportError:
    from pipeline import nlp_pipeline


def display_result(result):
    print("=" * 55)
    print("RESULTAT DOCTOAGENT v2")
    print("=" * 55)
    print("Texte    : " + result.original_text)
    print("Intent   : " + result.intent +
          " (conf: " + str(round(result.intent_confidence, 2)) + ")")
    print("Urgence  : " + result.urgency_label +
          " (" + str(result.urgency_score) + "/10" +
          ", conf: " + str(round(result.urgency_confidence, 2)) + ")")
    print("NER src  : " + result.ner_source)

    if result.entities:
        print("Entites  :")
        for ent in result.entities:
            print("   - " + ent['text'] + " [" + ent['label'] + "]")
    else:
        print("Entites  : Aucune")
    print("-" * 55)


def interactive_test():
    print("=" * 55)
    print("TESTEUR DOCTOAGENT v2")
    print("Urgency + Intent : VetBERT (F1=0.75 / 0.6977)")
    print("NER              : VetBERT NER (F1=0.78)")
    print("=" * 55)
    print("Tapez 'quitter' pour arreter.\n")

    while True:
        try:
            text = input("Entrez une question ou un symptome : ")
        except EOFError:
            break

        if text.lower() in ["quitter", "exit", "quit"]:
            break

        if not text.strip():
            continue

        print("\n--- Analyse en cours... ---")
        result = nlp_pipeline.process(text)
        display_result(result)


def single_text_test(text):
    result = nlp_pipeline.process(text)
    display_result(result)


def batch_test():
    tests = [
        # Urgences critiques
        ("URGENT my dog ate rat poison 2 hours ago",          ["emergency", "CRITICAL"]),
        ("My cat is having a seizure please help",             ["emergency", "CRITICAL"]),
        ("My dog suddenly collapsed and is not moving",        ["emergency", "CRITICAL"]),
        # Urgences moderees
        ("My golden retriever scratching his ear since morning", ["describe_symptom", "LOW/MODERATE"]),
        ("My persian cat refuses to drink since Tuesday",      ["describe_symptom", "MODERATE"]),
        ("My rabbit has been limping since last night",        ["describe_symptom", "MODERATE"]),
        # Questions conseil
        ("Is it safe to give my hamster fruit every day?",    ["ask_advice", "LOW"]),
        ("Should I take my dog to the vet for vomiting once?",["ask_advice", "LOW"]),
        # Entites rares (test NER)
        ("My budgie fell from his perch and cannot fly tonight", ["describe_symptom", "HIGH"]),
        ("Yorkshire terrier has a swollen paw after playing",  ["describe_symptom", "LOW"]),
        ("My old tabby cat seems very weak and confused today",["describe_symptom", "MODERATE"]),
        # Francais
        ("Mon chat vomit du sang depuis hier soir",            ["emergency", "HIGH"]),
        ("Mon chien a convulse, c'est urgent",                 ["emergency", "CRITICAL"]),
    ]

    print("=" * 65)
    print("BATCH TEST — DoctoAgent v2 (13 phrases)")
    print("=" * 65)

    correct_intent  = 0
    correct_urgency = 0

    for text, expected in tests:
        result = nlp_pipeline.process(text)

        intent_ok  = expected[0] in result.intent
        urgency_ok = expected[1].split("/")[0] in result.urgency_label

        if intent_ok:
            correct_intent += 1
        if urgency_ok:
            correct_urgency += 1

        status = "OK" if (intent_ok and urgency_ok) else "PARTIEL"

        print("\n[" + status + "] " + text[:60])
        print("  Intent  : " + result.intent + " (attendu: " + expected[0] + ")" +
              (" OK" if intent_ok else " FAUX"))
        print("  Urgence : " + result.urgency_label + " (attendu: " + expected[1] + ")" +
              (" OK" if urgency_ok else " FAUX"))
        print("  NER     : " + str([(e['text'], e['label']) for e in result.entities[:3]]))
        print("  Src NER : " + result.ner_source)

    print("\n" + "=" * 65)
    print("Score Intent  : " + str(correct_intent) + "/" + str(len(tests)))
    print("Score Urgency : " + str(correct_urgency) + "/" + str(len(tests)))
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Test DoctoAgent v2")
    parser.add_argument("--text",  type=str, default="",
                        help="Phrase unique a tester")
    parser.add_argument("--batch", action="store_true",
                        help="Batch test automatique sur 13 phrases")
    args = parser.parse_args()

    if args.batch:
        batch_test()
    elif args.text.strip():
        single_text_test(args.text.strip())
    else:
        interactive_test()


if __name__ == "__main__":
    main()