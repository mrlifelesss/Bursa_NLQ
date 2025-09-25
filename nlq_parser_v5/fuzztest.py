from rapidfuzz import fuzz

s1 = "לאומי"
s2 = "עין שלישית"

print("ratio:", fuzz.ratio(s1, s2))
print("partial_ratio:", fuzz.partial_ratio(s1, s2))
print("token_sort_ratio:", fuzz.token_sort_ratio(s1, s2))
print("token_set_ratio:", fuzz.token_set_ratio(s1, s2))
print("WRatio:", fuzz.WRatio(s1, s2))
