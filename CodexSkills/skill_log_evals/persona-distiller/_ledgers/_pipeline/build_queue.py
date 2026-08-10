#!/usr/bin/env python3
"""Build the deterministic distillation queue from the roster.
Output: _蒸馏队列.json  (ordered by family priority, then listed order).
Status is NOT stored here as truth; next_person.py derives 'done' live from
the registry (team-index.json) + Downloads ZIPs so it can never go stale."""
import json, os
OUT = "/Users/linzezhang/Downloads/蒸馏/_蒸馏队列.json"
# priority : (中文组名, family_id, [names in roster order])
FAM = {
 1: ("软件开发师","software-developer",["Dennis Ritchie","Ken Thompson","Linus Torvalds","Donald Knuth","Grace Hopper","Alan Kay","Guido van Rossum","Bjarne Stroustrup","Anders Hejlsberg","John Carmack","Tim Berners-Lee","Vint Cerf","Barbara Liskov","Leslie Lamport","Edsger Dijkstra","Tony Hoare","John McCarthy","Rob Pike","Margaret Hamilton","Douglas Engelbart"]),
 2: ("投资资本师","investor-capital-allocator",["Warren Buffett","Charlie Munger","Benjamin Graham","Philip Fisher","Peter Lynch","John Bogle","Ray Dalio","George Soros","Jim Simons","David Swensen","Howard Marks","Seth Klarman","Joel Greenblatt","Stanley Druckenmiller","Carl Icahn","John Templeton","Julian Robertson","Michael Steinhardt","Jesse Livermore"]),
 3: ("材料建工师","technical-engineer",["Nikolai Slavyanov","Nikolai Benardos","Elihu Thomson","C. L. Coffin","Comfort Avery Adams","Henry Bessemer","Henry Clifton Sorby","Adolf Martens","William Chandler Roberts-Austen","Edgar Bain","Robert Franklin Mehl","Walter Rosenhain","Pol Duwez","Morris Cohen","William D. Callister","Gustave Eiffel","Fazlur Rahman Khan","Ove Arup","Hardy Cross","Eduardo Torroja","Pier Luigi Nervi","Anton Tedesko","Stephen Timoshenko","Henry Maudslay","Joseph Whitworth","James Nasmyth","William Sellers","Waloddi Weibull","John Moubray","Stanley Nowlan"]),
 4: ("建造采购师","construction-procurement",["Charles M. Eastman","Patrick MacLeamy","Jerry Laiserin","Henry Gantt","Harold Kerzner","Russell Archibald","John Fondahl","James Kelley","Morgan Walker","Kenneth Humphreys","Eliyahu Goldratt","Peter Kraljic","Keith Oliver","Martin Christopher","Hau Lee","David Simchi-Levi"]),
 5: ("财务合规师","finance-compliance",["Luca Pacioli","William Paton","A. C. Littleton","Robert Kaplan","Harry Markowitz","William Sharpe","Eugene Fama","Robert Merton","Myron Scholes","Fischer Black","Franco Modigliani","Merton Miller","Herbert Heinrich","James Reason","Charles Perrow","Nancy Leveson","Sidney Dekker","W. Edwards Deming","Joseph Juran","Walter Shewhart","Kaoru Ishikawa","Genichi Taguchi"]),
 6: ("政治法律师","political-legal",["Cicero","Hugo Grotius","William Blackstone","Oliver Wendell Holmes Jr.","Hans Kelsen","H. L. A. Hart","Ronald Dworkin","Louis Brandeis","John Marshall","Ruth Bader Ginsburg","Solon","Abraham Lincoln","Otto von Bismarck","Nelson Mandela","Lee Kuan Yew","Winston Churchill","Niccolo Machiavelli","Thomas Jefferson"]),
 7: ("客户营销师","customer-marketing",["Philip Kotler","David Ogilvy","Claude C. Hopkins","Edward Bernays","Theodore Levitt","Seth Godin","Byron Sharp","Al Ries","Jack Trout","Leo Burnett","Bill Bernbach","Rosser Reeves","Regis McKenna","Don Peppers","Martha Rogers","Geoffrey Moore","David Aaker","Kevin Lane Keller","Sergio Zyman","Mary Wells Lawrence"]),
 8: ("创业经营师","entrepreneur-operator",["Henry Ford","Alfred Sloan","Konosuke Matsushita","Akio Morita","Soichiro Honda","Ray Kroc","Ingvar Kamprad","Jack Welch","Herb Kelleher","Jeff Bezos","Steve Jobs","Peter Drucker","Jim Collins","Satya Nadella","Mary Barra","Indra Nooyi","Jamie Dimon","Richard Branson"]),
 9: ("艺术设计师","art-designer",["Leonardo da Vinci","Michelangelo","Pablo Picasso","Dieter Rams","Paul Rand","Milton Glaser","Massimo Vignelli","Saul Bass","Josef Albers","Walter Gropius","Le Corbusier","Frank Lloyd Wright","Charles Eames","Raymond Loewy","Henry Dreyfuss","Buckminster Fuller","Zaha Hadid","Tadao Ando","Kenya Hara","Coco Chanel"]),
 10: ("思想教育师","thinker-educator",["Confucius","Socrates","Plato","Aristotle","Immanuel Kant","Jean-Jacques Rousseau","Johann Pestalozzi","Friedrich Frobel","John Amos Comenius","John Dewey","Maria Montessori","Lev Vygotsky","Jean Piaget","Paulo Freire","Benjamin Bloom","Howard Gardner","Seymour Papert","John Hattie"]),
 11: ("医疗护理师","healthcare-nursing",["Hippocrates","Galen","Andreas Vesalius","William Harvey","Edward Jenner","Ignaz Semmelweis","Louis Pasteur","Robert Koch","Joseph Lister","Rudolf Virchow","William Osler","Alexander Fleming","Florence Nightingale","Virginia Henderson","Hildegard Peplau","Jean Watson","Clara Barton","Elizabeth Blackwell","Michael DeBakey","Atul Gawande","Paul Farmer"]),
 12: ("农林牧渔师","agriculture-fishery",["Norman Borlaug","Yuan Longping","Justus von Liebig","Gregor Mendel","Nikolai Vavilov","George Washington Carver","Luther Burbank","M. S. Swaminathan","Albert Howard","Masanobu Fukuoka","Wes Jackson","Gifford Pinchot","Aldo Leopold","Jay Lush","Temple Grandin"]),
}
q = []
for prio in sorted(FAM):
    zh, fid, names = FAM[prio]
    for order, name in enumerate(names, 1):
        q.append({"name": name, "family_zh": zh, "family_id": fid, "priority": prio, "order": order})
json.dump({"generated_note":"target roster; done-state derived live by next_person.py",
           "total": len(q), "queue": q}, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print(json.dumps({"total": len(q), "by_family": {FAM[p][0]: sum(1 for x in q if x['priority']==p) for p in sorted(FAM)}}, ensure_ascii=False, indent=1))
