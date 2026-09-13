"""Lab-safety and lab-procedure reference corpus for the RAG grounding layer.

Each entry is a short, self-contained passage synthesized from public lab-safety
guidance. `source` names the reference material the passage is based on; the text
is a condensed paraphrase, not a verbatim quote. Primary bases:

- OSHA, Laboratory Safety Guidance, U.S. Dept. of Labor (OSHA 3404-11R).
- National Research Council, "Prudent Practices in the Laboratory" (2011).
- ACS, "Safety in Academic Chemistry Laboratories".
- NFPA 45 / NFPA 70 fire & electrical safety fundamentals.
- CDC/NIH, "Biosafety in Microbiological and Biomedical Laboratories" (BMBL).
"""

CORPUS = [
    {
        "id": "chemical-hygiene-plan",
        "title": "Chemical Hygiene Plan (CHP)",
        "source": "OSHA Laboratory Standard 29 CFR 1910.1450; Prudent Practices ch. 1",
        "text": (
            "Every laboratory must maintain a written Chemical Hygiene Plan (CHP) that "
            "describes standard operating procedures, control measures, and the designated "
            "Chemical Hygiene Officer. The CHP must cover exposure limits, fume hood use, "
            "engineering controls, PPE requirements, and procedures for particularly hazardous "
            "substances. Employees and students must be trained on the CHP before starting work "
            "and whenever new hazards are introduced. The plan must be reviewed at least "
            "annually and updated when procedures or regulations change."
        ),
    },
    {
        "id": "ppe",
        "title": "Personal Protective Equipment (PPE)",
        "source": "OSHA Laboratory Safety Guidance; Prudent Practices ch. 6",
        "text": (
            "Minimum PPE in a teaching or research lab includes safety goggles or glasses, a "
            "laboratory coat, and chemically resistant gloves matched to the chemicals in use. "
            "Goggles (not just glasses) are required when splash hazards exist. Gloves must be "
            "removed before touching phones, door handles, or computers, and they do not "
            "substitute for hand washing. Contact lenses do not provide eye protection and must "
            "be worn with goggles. Open-toed shoes, shorts, and loose clothing are not permitted "
            "in the lab. PPE is the last line of defense after elimination, substitution, and "
            "engineering controls."
        ),
    },
    {
        "id": "fire-safety",
        "title": "Fire Safety and Extinguishers",
        "source": "NFPA 10; OSHA 29 CFR 1910.157; Prudent Practices ch. 6.C",
        "text": (
            "Fire extinguishers are classified by the fire type: Class A (ordinary combustibles "
            "such as paper and wood), Class B (flammable liquids like acetone or ethanol), "
            "Class C (energized electrical equipment), and Class D (combustible metals). "
            "Operate an extinguisher with the PASS technique: Pull the pin, Aim at the base of "
            "the fire, Squeeze the handle, and Sweep side to side. Never fight a fire larger "
            "than a wastebasket; instead evacuate, close doors behind you, pull the fire alarm, "
            "and call for help. Know the location of the two nearest exits and the assembly "
            "point before starting any experiment."
        ),
    },
    {
        "id": "electrical-safety",
        "title": "Electrical Safety in the Lab",
        "source": "NFPA 70 (National Electrical Code); Prudent Practices ch. 6.F",
        "text": (
            "Inspect cords, plugs, and equipment for fraying or damage before use. Never use "
            "damaged equipment, and never repair it yourself; tag it out and report it. Keep "
            "water and other liquids away from electrical outlets and equipment. Use "
            "ground-fault circuit interrupters (GFCI) for circuits near water sources. "
            "When probing circuits with an oscilloscope or multimeter, confirm the instrument's "
            "voltage and current ratings, use properly insulated probes, and never defeat a "
            "ground pin. One hand should be kept out of the circuit whenever possible to reduce "
            "the risk of a current path through the chest."
        ),
    },
    {
        "id": "bunsen-burner",
        "title": "Bunsen Burner Procedure",
        "source": "ACS Safety in Academic Chemistry Laboratories; standard lab manuals",
        "text": (
            "Before lighting a Bunsen burner, clear the area of flammable solvents and paper, "
            "tie back loose hair and clothing, and check that the gas tubing has no cracks and "
            "is firmly attached to both the gas outlet and the burner. Light the match (or "
            "striker) first, then slowly open the gas valve; never open the gas first. A safe, "
            "hot flame is blue with a lighter inner cone; a yellow, smoky flame indicates "
            "incomplete combustion and poor air mixing. Never leave a lit burner unattended, "
            "and always turn off the gas at the outlet valve when finished."
        ),
    },
    {
        "id": "glassware",
        "title": "Glassware Handling and Broken-Glass Disposal",
        "source": "Prudent Practices ch. 6.C; standard lab manuals",
        "text": (
            "Inspect glassware for chips, cracks, and star cracks before use; damaged glassware "
            "can fail under vacuum or heat. Never use bare hands to insert glass tubing into a "
            "stopper — lubricate with water or glycerol and protect hands with a towel while "
            "twisting gently. Hot glassware looks identical to cold glassware: allow it to cool "
            "on an insulated mat and label it as hot. Broken glass goes into a dedicated "
            "puncture-resistant 'sharps' container, never into regular trash bins, and "
            "never bare-handed — use a brush and dustpan."
        ),
    },
    {
        "id": "acid-base",
        "title": "Acid and Base Handling",
        "source": "Prudent Practices ch. 6.D; ACS Safety in Academic Chemistry Laboratories",
        "text": (
            "When diluting concentrated acids, always add acid to water, never water to acid: "
            "pouring water into concentrated acid can cause violent boiling and splashing. "
            "Dilute slowly, with stirring, in a heat-resistant container. Acids and bases are "
            "stored separately, and corrosive reagents are handled in a fume hood when "
            "volatile. Spills on skin are flushed with copious water for at least 15 minutes. "
            "Neutralize small spills only with the approved spill kit; never neutralize a "
            "spill on skin."
        ),
    },
    {
        "id": "sds",
        "title": "Safety Data Sheets (SDS)",
        "source": "OSHA Hazard Communication Standard 29 CFR 1910.1200",
        "text": (
            "Every hazardous chemical in the lab must have a Safety Data Sheet (SDS) available "
            "to users. The SDS is organized into 16 sections, including hazards identification "
            "(Section 2), first-aid measures (Section 4), fire-fighting measures (Section 5), "
            "handling and storage (Section 7), and exposure controls and PPE (Section 8). Read "
            "the SDS before working with a chemical you have not used before, and pay special "
            "attention to the signal word (Danger or Warning), hazard pictograms, and "
            "incompatible materials."
        ),
    },
    {
        "id": "fume-hood",
        "title": "Fume Hood Use",
        "source": "Prudent Practices ch. 9.C; OSHA Laboratory Safety Guidance",
        "text": (
            "Work with volatile, toxic, or strong-smelling chemicals inside a fume hood with "
            "the sash at the marked safe operating height. Keep the work at least 15 cm inside "
            "the hood face, and avoid rapid arm movements that disturb the air curtain. Do not "
            "store chemicals permanently in the hood — clutter disrupts airflow and blocks the "
            "baffles. Confirm airflow before starting work, typically by watching the "
            "sash-mounted indicator or a tissue strip drawn inward. Lower the sash fully when "
            "the hood is unattended."
        ),
    },
    {
        "id": "eyewash-shower",
        "title": "Emergency Eyewash and Safety Shower",
        "source": "ANSI Z358.1; Prudent Practices ch. 6.C",
        "text": (
            "In case of a chemical splash to the eyes, proceed immediately to the nearest "
            "eyewash station and flush both eyes for at least 15 minutes, holding the eyelids "
            "open with your fingers. For large body splashes, use the safety shower and remove "
            "contaminated clothing while flushing. Do not stop to remove contact lenses first — "
            "the flushing action will take them out. Report the incident to the instructor or "
            "supervisor and seek medical evaluation after flushing, even if you feel fine. "
            "Eyewash and shower stations are checked weekly for water flow."
        ),
    },
    {
        "id": "chemical-spills",
        "title": "Chemical Spill Response",
        "source": "Prudent Practices ch. 6.C; OSHA Laboratory Safety Guidance",
        "text": (
            "Small spills of low-toxicity liquids can be cleaned with the lab's spill kit: "
            "contain the spill, absorb it with inert material, collect the residue, and dispose "
            "of it as hazardous waste. For flammable, corrosive, or toxic spills, alert "
            "everyone, evacuate if vapors are present, and notify the instructor or safety "
            "officer — do not attempt cleanup alone. Never use paper towels on acid spills "
            "without a neutralizing agent. Mercury spills require a dedicated mercury spill kit. "
            "Every spill, however small, must be reported."
        ),
    },
    {
        "id": "waste-disposal",
        "title": "Laboratory Waste Segregation",
        "source": "Prudent Practices ch. 8; local institutional hazardous-waste policy",
        "text": (
            "Laboratory waste is segregated at the point of generation: chemical waste is "
            "collected in labeled, compatible containers (never in unlabeled beakers), "
            "sharps and broken glass go into puncture-resistant containers, and biological "
            "waste is autoclaved or collected per biosafety level. Halogenated and "
            "non-halogenated solvents are kept in separate containers. Never pour chemicals "
            "down the sink unless the lab's written procedure explicitly permits it, and never "
            "mix incompatible wastes (acids with bases, oxidizers with organics). Containers "
            "are kept closed except when actively adding waste."
        ),
    },
    {
        "id": "autoclave",
        "title": "Autoclave Operation",
        "source": "CDC/NIH BMBL Appendix; standard microbiology lab manuals",
        "text": (
            "An autoclave sterilizes using saturated steam at 121 degrees Celsius and 15 psi "
            "for a validated hold time, commonly 15-30 minutes depending on load. Loosen lids "
            "and add a little water to bags so steam can penetrate. Do not autoclave sealed "
            "containers, flammable liquids, bleach, or materials that generate toxic gases. "
            "Wear heat-resistant gloves and a face shield when opening the door, open it "
            "slowly away from yourself, and let the load cool before handling. Verify each "
            "cycle with chemical or biological indicators and record the run in the log."
        ),
    },
    {
        "id": "centrifuge",
        "title": "Centrifuge Safety",
        "source": "Prudent Practices ch. 6.H; standard lab manuals",
        "text": (
            "Centrifuge rotors must always be balanced: tubes of equal mass are placed "
            "opposite each other, and a balance tube of the same mass is used for odd numbers "
            "of samples. An unbalanced rotor can walk off the bench or fail catastrophically. "
            "Never open the lid while the rotor is spinning, and never stop a spinning rotor "
            "with your hand. Inspect tubes for cracks before use, and use the correct rotor "
            "and speed for the tube material. If the machine vibrates or makes unusual noise, "
            "stop the run immediately and report it."
        ),
    },
    {
        "id": "gas-cylinders",
        "title": "Compressed Gas Cylinder Handling",
        "source": "OSHA 29 CFR 1910.101; Prudent Practices ch. 6.E",
        "text": (
            "Compressed gas cylinders are stored upright, secured with a chain or strap, and "
            "with the valve cap in place when not in use. Never drag, drop, or roll cylinders "
            "— use a cylinder cart. Open valves slowly, stand to the side (not in front of) the "
            "regulator, and use the correct regulator for the gas. Flammable gases such as "
            "hydrogen and acetylene are kept away from oxidizers and ignition sources. A "
            "leaking cylinder is evacuated and reported; never attempt to repair a cylinder "
            "valve yourself."
        ),
    },
    {
        "id": "soldering",
        "title": "Soldering Safety",
        "source": "Standard electronics lab manuals; OSHA general duty clause guidance",
        "text": (
            "Soldering irons operate at 300-400 degrees Celsius and cause severe burns: always "
            "return the iron to its stand when not in use and grip it only by the insulated "
            "handle. Solder in a well-ventilated area or under fume extraction because rosin "
            "flux fumes are respiratory irritants, and lead-based solder requires washing hands "
            "before eating or drinking. Never flick molten solder off the tip — use a damp "
            "sponge or brass wool. Unplug the iron and let it cool before leaving the bench, "
            "and keep the power cord clear of the hot tip."
        ),
    },
    {
        "id": "laser-safety",
        "title": "Laser Safety Classes",
        "source": "ANSI Z136.1; Prudent Practices ch. 6.G",
        "text": (
            "Lasers are classified by hazard: Class 1 is inherently safe, Class 2 (up to 1 mW, "
            "visible) relies on the blink reflex, Class 3R and 3B can injure eyes even in brief "
            "direct exposure, and Class 4 can burn skin and ignite materials and also produces "
            "hazardous diffuse reflections. Wear laser-safety goggles matched to the laser's "
            "wavelength and optical density, remove reflective jewelry, and never look directly "
            "into the beam or aim it at eye level. Class 3B and 4 lasers are used in "
            "interlocked, signposted areas only."
        ),
    },
    {
        "id": "microscope",
        "title": "Microscope Use and Care",
        "source": "Standard biology lab manuals",
        "text": (
            "Carry a microscope with one hand under the base and the other on the arm; never "
            "carry it by the eyepiece or stage. Start focusing with the lowest-power objective "
            "using the coarse adjustment, then switch to higher objectives and use only the "
            "fine adjustment — using the coarse knob at high power can crack the slide and "
            "scratch the objective lens. Clean lenses only with lens paper and lens cleaner, "
            "never with paper towels or water. Oil-immersion lenses (100x) require immersion "
            "oil and must be wiped clean immediately after use, then covered when stored."
        ),
    },
    {
        "id": "titration",
        "title": "Titration Procedure",
        "source": "Standard chemistry lab manuals",
        "text": (
            "A titration measures the concentration of an unknown solution by reacting it with "
            "a standard solution of known concentration. Rinse the burette with the titrant, "
            "fill it above the zero mark, and open the stopcock briefly to expel air bubbles "
            "from the tip — bubbles cause volume-reading errors. Record the initial burette "
            "reading to 0.01 mL, add a few drops of indicator, and swirl the flask while "
            "adding titrant dropwise near the endpoint. The endpoint is the first permanent "
            "color change; stop, record the final volume, and repeat at least twice for "
            "reproducible results."
        ),
    },
    {
        "id": "first-aid",
        "title": "Basic Lab First Aid",
        "source": "Prudent Practices ch. 6.C; institutional emergency procedures",
        "text": (
            "Every lab has a first-aid kit and knows the location of the nearest eyewash, "
            "safety shower, and fire extinguisher. For cuts, apply direct pressure with a clean "
            "dressing and seek medical help for deep or heavily bleeding wounds. For thermal "
            "burns, cool the area under gently running cool water for 10-20 minutes; do not "
            "apply ice, ointments, or adhesive dressings to serious burns. For chemical "
            "exposure, flush with water for at least 15 minutes and bring the chemical's SDS "
            "to medical personnel. All injuries and near-misses must be reported to the "
            "instructor or supervisor and recorded in the incident log."
        ),
    },
]
