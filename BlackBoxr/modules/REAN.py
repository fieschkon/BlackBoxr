import spacy
from spacy.matcher import Matcher

nlp = spacy.load('en_core_web_lg')

def isPassive(sentence):
    matcher = Matcher(nlp.vocab)
    doc = nlp(sentence)
    #sents = list(doc.sents)
    matcher.add('Passive', [[{'DEP':'nsubjpass'},{'DEP':'aux','OP':'*'},{'DEP':'auxpass'},{'TAG':'VBN'}]])
    matches = matcher(doc)
    return len(matches) > 0

def similarity(sentenceA, sentenceB):
    
    doc1 = nlp(' '.join([str(t) for t in nlp(sentenceA) if not t.is_stop]))
    
    doc2 = nlp(' '.join([str(t) for t in nlp(sentenceB) if not t.is_stop]))
    return doc1.similarity(doc2)


print(isPassive('''The kernel is run by the processor.''' ))
print(isPassive('''The processor runs the kernel''' ))
print(similarity("A calendar shall be available to help with entering the flight date.", "The system shall display a pop-up calendar when entering the flight date."))
print(similarity("I like ice cream", "I fucking hate chicken tenders"))

testlist = [('As a User, I want to sign up via email and password so that I can access my account.', 'There has to be a way to authenticate.')]