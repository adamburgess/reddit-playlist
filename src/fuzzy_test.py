from fuzzywuzzy import fuzz

print(fuzz.partial_ratio("Ari Ari (Indian Street Metal)".lower(), "Indian Street Metal".lower()))
print(fuzz.partial_ratio("I’ll Keep You Safe (feat.Shiloh)".lower(), "I'll Keep You Safe".lower()))
print(fuzz.partial_ratio("sagun".lower(), "Sagun".lower()))
print(fuzz.partial_ratio("we've never met but, can we have a coffee or something?".lower(), "We've Never Met but Can We Have a Cup of Coffee or Something".lower()))
print(fuzz.partial_ratio("Mr. Know-It-All (Young the Giant cover)".lower(), "Mr. Know-It-All".lower()))
print(fuzz.partial_ratio("op-1: plswaveback".lower(), "Plswaveback".lower()))
print(fuzz.partial_ratio("In Hell I'll Be Ian Good Company by The Dead South".lower(), "In Hell I'll Be in Good Company by The Dead South".lower()))
print(fuzz.partial_ratio("Kerrin Connolly".lower(), "Leonard Cohen".lower()))
print(fuzz.partial_ratio("Melody of Pi".lower(), "Song from Phi".lower()))