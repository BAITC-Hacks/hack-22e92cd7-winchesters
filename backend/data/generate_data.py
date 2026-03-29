"""Generate synthetic candidate dataset for InVision U demo.

Includes diverse profiles with edge cases:
- Strong essay / weak GPA
- Strong GPA / weak essay
- AI-generated essay
- Outstanding all-around
- Strong growth trajectory despite disadvantages
- Good "seller" with average substance
"""

import json
import os

CANDIDATES = [
    {
        "id": "c-001",
        "name": "Aigerim Tastanova",
        "age": 17,
        "application": {
            "education": {
                "school_type": "lyceum",
                "gpa": 3.9,
                "academic_achievements": [
                    "National Math Olympiad - 2nd place",
                    "Regional Science Fair - 1st place",
                    "Presidential Scholarship recipient"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Debate Club", "duration_months": 36, "role": "president"},
                {"activity": "Volunteer tutoring for younger students", "duration_months": 24, "role": "organizer"},
                {"activity": "School newspaper", "duration_months": 18, "role": "editor"}
            ],
            "projects": [
                {"name": "Free math tutoring program for rural schools", "role": "founder", "impact": "Reached 150+ students in 5 villages over 2 years"}
            ],
            "languages": ["Kazakh", "Russian", "English"],
            "skills": ["public speaking", "mathematics", "project management", "writing"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "When I started tutoring kids in Zhambyl village, I thought math was universal — numbers don't need translation. I was wrong. The children didn't struggle with equations; they struggled with believing they deserved to learn them. Most had never met anyone who went to university. I remember one girl, Madina, who kept erasing her correct answers because she assumed they must be wrong.\n\nI realized that teaching math wasn't enough. I needed to teach belief. So I changed my approach completely. Instead of lecturing, I asked them to teach each other. Madina became the 'expert' on fractions because I noticed she quietly solved them faster than anyone. When her classmates came to her for help, I watched something shift in her eyes.\n\nThis experience broke something in me — the idea that leadership means having answers. Real leadership, I learned, is about seeing what others can't see in themselves and creating conditions where they discover it. I failed many times that first semester. My lesson plans were terrible. Three kids dropped out because I couldn't make it interesting enough. But each failure taught me to listen more and assume less.\n\nThe program now runs in five villages with twelve volunteer tutors I trained. I don't run the sessions anymore — the tutors do. And that's the point. The best leadership makes itself unnecessary."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: I've built something small that works in five villages. I want to learn how to think at a scale where I can change how education works across Kazakhstan. inVision U isn't just a university — it's a community of people who believe that Central Asia can lead, not just follow. I want to be part of building that future.\n\nQ: What's your biggest weakness?\nA: I take on too much and then feel guilty asking for help. Last year I almost burned out running the tutoring program, school newspaper, and debate club simultaneously. I've learned to delegate but it's still hard for me to let go of control.\n\nQ: Tell us about a time you failed.\nA: My first three tutoring sessions were disasters. I prepared university-level explanations for 12-year-olds. The kids were bored and confused. One boy told me 'you talk like a textbook.' That was the wake-up call I needed to completely redesign my approach.",
        "recommendation_summary": "Aigerim is one of the most driven and empathetic students I have taught in 20 years. She combines intellectual rigor with genuine care for others. Her tutoring initiative demonstrates real leadership — she built something sustainable, not just impressive for a CV."
    },
    {
        "id": "c-002",
        "name": "Damir Kozhaev",
        "age": 18,
        "application": {
            "education": {
                "school_type": "public",
                "gpa": 3.2,
                "academic_achievements": [
                    "Regional robotics competition - 3rd place"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Robotics club", "duration_months": 30, "role": "member"},
                {"activity": "Part-time job at family repair shop", "duration_months": 48, "role": "technician"}
            ],
            "projects": [
                {"name": "Automated irrigation system for grandmother's garden", "role": "sole builder", "impact": "Reduced water usage by 40%, built from recycled parts costing under $30"},
                {"name": "Repair workshop YouTube channel", "role": "creator", "impact": "1,200 subscribers, teaches basic electronics repair in Kazakh language"}
            ],
            "languages": ["Kazakh", "Russian"],
            "skills": ["electronics repair", "robotics", "practical engineering", "resourcefulness"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "I live in a small town where the nearest service center is two hours away. When neighbors' phones or kettles break, they come to us. My grandmother has run a repair shop for twenty years, and I've been helping her after school since I was thirteen.\n\nAt first I just handed her tools. Then I started figuring things out myself — watching YouTube videos, reading forums. The first phone I fixed on my own was an old Samsung with a cracked screen. I ordered the part from Almaty, waited two weeks, and spent three hours replacing the screen following a video tutorial. When it turned on, I nearly shouted.\n\nGradually, repair turned into something bigger. I noticed my grandmother's garden had a watering problem — not enough water, and carrying buckets was hard for her. I built a drip irrigation system from old hoses and plastic bottles. It's not perfect, but grandmother says the harvest improved.\n\nThen I made a similar system for a neighbor. Then another one. I started filming videos about how to make simple things from available materials — fix a faucet, build irrigation, replace a socket. The channel is small, but people write that it helps.\n\nI don't consider myself a leader. I just love fixing things and helping people around me. But maybe leadership is exactly that — seeing what people nearby need and doing it without waiting to be asked."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: I want to learn how to build things properly, not just from scrap materials. I understand how mechanisms work, but I lack an engineering education. There's no way to study this in our town, but at inVision U I could grow.\n\nQ: What's your biggest weakness?\nA: I'm bad at asking for help. I'm used to doing everything myself, and sometimes I spend three days on a task when I could have asked someone in five minutes. Working on it.\n\nQ: Tell us about a time you failed.\nA: I once tried to fix a washing machine even though I had no idea how they work. Took it apart, couldn't put it back together, and the neighbor had to call a repairman from the city. I was very embarrassed. Since then I don't take on things I'm not sure about until I study the topic first.",
        "recommendation_summary": "Damir is an exceptionally practical and self-reliant student. His ability to independently master technical skills and apply them to help others shows maturity and responsibility."
    },
    {
        "id": "c-003",
        "name": "Asel Muratova",
        "age": 17,
        "application": {
            "education": {
                "school_type": "private",
                "gpa": 3.95,
                "academic_achievements": [
                    "National Biology Olympiad - 1st place",
                    "International Science Olympiad - participant",
                    "School valedictorian",
                    "Cambridge English Certificate - C1"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Student council", "duration_months": 24, "role": "vice-president"},
                {"activity": "Biology research internship at university lab", "duration_months": 6, "role": "intern"},
                {"activity": "Piano", "duration_months": 96, "role": "performer"}
            ],
            "projects": [],
            "languages": ["Kazakh", "Russian", "English", "Turkish"],
            "skills": ["biology", "research methodology", "academic writing", "piano"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "Leadership is a multifaceted concept that encompasses various dimensions of personal and professional development. Throughout my academic journey, I have encountered numerous challenges that have significantly contributed to my growth as a leader and shaped my understanding of what it means to guide others toward a common goal.\n\nOne particularly transformative experience occurred during my participation in the National Biology Olympiad. The preparation process was rigorous and demanding, requiring me to develop advanced study strategies and time management skills. I demonstrated leadership by organizing study groups for my fellow competitors, creating comprehensive review materials, and fostering a collaborative learning environment.\n\nThe challenge of balancing academic excellence with extracurricular commitments taught me valuable lessons about prioritization and resilience. As vice-president of the student council, I implemented several initiatives aimed at improving student engagement and academic support systems. These experiences reinforced my belief that effective leadership requires both strategic thinking and emotional intelligence.\n\nFurthermore, my research internship at the university laboratory provided me with insights into scientific leadership and the importance of mentorship. Working alongside experienced researchers, I learned that true leaders are those who empower others to reach their full potential while maintaining the highest standards of integrity and excellence.\n\nIn conclusion, my journey has taught me that leadership is not merely about achieving personal success, but about creating meaningful impact and inspiring others to pursue their aspirations with determination and purpose."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: I believe inVision U represents a unique opportunity to combine academic excellence with practical impact. The university's mission aligns with my personal values of innovation and leadership development.\n\nQ: What's your biggest weakness?\nA: I sometimes focus too much on perfection, which can slow down my progress. I'm learning to balance quality with efficiency.\n\nQ: Tell us about a time you failed.\nA: During my first science olympiad in 9th grade, I didn't advance past the regional round. I analyzed my mistakes systematically and developed a more structured preparation approach, which ultimately led to my national-level success.",
        "recommendation_summary": "Asel is an exceptional student with outstanding academic credentials. She is disciplined, articulate, and consistently performs at the highest level. She would be an asset to any academic institution."
    },
    {
        "id": "c-004",
        "name": "Nursultan Akhmetov",
        "age": 18,
        "application": {
            "education": {
                "school_type": "gymnasium",
                "gpa": 3.6,
                "academic_achievements": [
                    "Regional History Competition - 1st place",
                    "City-level debate tournament - finalist"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Youth Parliament program", "duration_months": 18, "role": "delegate"},
                {"activity": "Community clean-up initiative", "duration_months": 12, "role": "co-founder"},
                {"activity": "School basketball team", "duration_months": 36, "role": "captain"}
            ],
            "projects": [
                {"name": "Plastic-free campus campaign", "role": "co-founder", "impact": "Eliminated single-use plastic in school cafeteria, adopted by 3 neighboring schools"},
                {"name": "Youth civic education workshops", "role": "lead facilitator", "impact": "Conducted 15 workshops reaching 300+ students on democratic participation"}
            ],
            "languages": ["Kazakh", "Russian", "English"],
            "skills": ["public speaking", "community organizing", "civic education", "team sports"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "Last year our school cafeteria was drowning in plastic. Bottles, wrappers, bags — every lunch produced a small mountain of waste. Everyone complained. Nobody did anything. I decided to be the one who did something, even though I had no idea how.\n\nMy friend Arman and I started the 'Plastic-free Campus' campaign. We thought it would be simple — just ask the cafeteria to switch to reusable containers. We were naive. The cafeteria manager said it was too expensive. The principal said it was 'not a priority.' Half the students thought we were being annoying.\n\nSo we changed tactics. Instead of asking for permission, we proved it was possible. We calculated the cost difference between disposable and reusable options over a year — reusable was actually cheaper. We made a presentation to the school board with real numbers. We organized a 'Zero Waste Week' challenge where classes competed to produce the least trash.\n\nThe turning point was when the local newspaper covered our Zero Waste Week. Suddenly the principal cared. The cafeteria manager found budget. Three other schools reached out asking how to replicate our program.\n\nWhat I learned is that leadership isn't about authority — it's about persistence and making the invisible visible. Nobody saw the plastic problem as solvable until we showed them it was. The hardest part wasn't the logistics. It was convincing people that change was worth the inconvenience.\n\nI still don't think of myself as a 'leader' — I think of myself as someone who gets irritated by problems and can't stop until they're fixed."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: I want to work on problems bigger than a school cafeteria. I see so many issues in my community — waste management, youth disengagement, lack of civic education. inVision U seems like a place where I'll meet people who also can't sit still when they see something broken, and where I'll learn the tools to fix things at a systemic level.\n\nQ: What's your biggest weakness?\nA: I can be impatient. When I see a problem, I want to fix it immediately, and I sometimes rush into action before fully thinking through the plan. Arman, my co-founder, has taught me to slow down and strategize more.\n\nQ: Tell us about a time you failed.\nA: Our first attempt at the civic education workshops was a failure. I prepared a lecture-style presentation and the students were bored out of their minds. I realized I was doing exactly what bad teachers do. So I redesigned the workshops as interactive simulations — mock elections, budget allocation games, debate circles. Attendance tripled.",
        "recommendation_summary": "Nursultan is a natural leader who leads by doing, not by talking. His plastic-free campaign showed initiative, strategic thinking, and the ability to rally others. He has a rare combination of passion and pragmatism."
    },
    {
        "id": "c-005",
        "name": "Kamila Yessenova",
        "age": 17,
        "application": {
            "education": {
                "school_type": "public",
                "gpa": 3.4,
                "academic_achievements": [
                    "School Art Competition - 1st place"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Art therapy volunteer at children's hospital", "duration_months": 18, "role": "volunteer"},
                {"activity": "Instagram art account", "duration_months": 24, "role": "creator"}
            ],
            "projects": [
                {"name": "Art therapy workshops for hospitalized children", "role": "initiator", "impact": "Weekly sessions for 6 months, hospital staff reported improved patient morale"}
            ],
            "languages": ["Kazakh", "Russian"],
            "skills": ["visual arts", "empathy", "creative thinking", "social media"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "I don't think I'm a leader. I'm an artist. But maybe that's the same thing sometimes.\n\nSix months ago I started visiting the children's ward at City Hospital No. 4. I brought colored pencils and paper. I didn't have a plan or a program. I just knew that kids in hospitals are bored and scared, and drawing helps with both.\n\nThe first time, only two children participated. One boy, Timur, who was 8 and recovering from surgery, wouldn't even look at me. He stared at the wall. I sat next to him and started drawing — not talking, just drawing. After twenty minutes he asked for a blue pencil. We drew together in silence for an hour.\n\nTimur started waiting for my visits. Then other kids did too. The nurses noticed that the children were calmer on the days I came. One nurse cried and told me that Timur had barely spoken to anyone for weeks before I came.\n\nI realized that sometimes leadership looks nothing like what we expect. It's not speeches and campaigns. Sometimes it's sitting quietly with someone and handing them a blue pencil.\n\nThe challenge wasn't the hospital — it was myself. I had to overcome my fear of seeing sick children, my doubt that art could actually help, and my shyness about taking up space in a medical setting. Each visit was emotionally draining. Some weeks I didn't want to go. But then I'd remember Timur's face when he finished his first drawing — a spaceship going somewhere far away from the hospital — and I'd pack my pencils and go.\n\nI now run weekly sessions and trained three other student volunteers. The hospital asked me to design murals for the pediatric wing. It's still small. But it's real."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: I want to learn how to turn something small and personal into something that can help more people. I know art therapy works — I've seen it. But I don't know how to scale it, fund it, or make it a real program. I need those skills.\n\nQ: What's your biggest weakness?\nA: I'm not great at academics. My grades are average because I spend a lot of time on art and volunteering. I also struggle with math and science. I'm worried I might not keep up at university.\n\nQ: Tell us about a time you failed.\nA: I tried to organize an art exhibition to raise money for hospital supplies. Almost nobody came. I promoted it only on my Instagram and didn't reach beyond my own circle. I learned that having a good cause isn't enough — you need to know how to communicate it to the right audience.",
        "recommendation_summary": "Kamila is quiet but deeply impactful. Her art therapy initiative at the hospital shows maturity and emotional intelligence beyond her years. She may not have the strongest academic profile, but her capacity for empathy and creative problem-solving is remarkable."
    },
    {
        "id": "c-006",
        "name": "Arman Bekov",
        "age": 18,
        "application": {
            "education": {
                "school_type": "private",
                "gpa": 3.85,
                "academic_achievements": [
                    "National Economics Olympiad - 3rd place",
                    "MUN Best Delegate award",
                    "IELTS 7.5"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Model United Nations", "duration_months": 24, "role": "secretary-general"},
                {"activity": "School business club", "duration_months": 18, "role": "president"},
                {"activity": "Tennis", "duration_months": 60, "role": "player"}
            ],
            "projects": [
                {"name": "Student marketplace app concept", "role": "team lead", "impact": "Won school startup competition, concept stage only"}
            ],
            "languages": ["Russian", "English", "Kazakh"],
            "skills": ["public speaking", "economics", "negotiation", "business planning"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "As Secretary-General of our school's Model United Nations, I faced the challenge of organizing a conference for 200 delegates from 15 schools. The logistics were overwhelming — venues, schedules, committee topics, judge recruitment. Two weeks before the event, our venue cancelled.\n\nI immediately convened an emergency meeting with my team of 12 organizers. We brainstormed alternatives and within 48 hours secured a new venue at the city cultural center. I delegated tasks efficiently: communications team handled school notifications, logistics team managed the new floor plan, and I personally called every judge to confirm the venue change.\n\nThe conference was a success. We received positive feedback from 95% of participants in our post-event survey. The experience taught me that leadership means staying calm under pressure, making quick decisions with incomplete information, and trusting your team to execute.\n\nI also learned the importance of contingency planning. Now I always prepare backup options for critical elements of any project I manage. This systematic approach to risk management has become a cornerstone of my leadership philosophy.\n\nFurthermore, this experience reinforced my passion for international relations and diplomacy, fields where leadership and negotiation skills are paramount."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: inVision U combines academic rigor with entrepreneurial thinking. I want to build businesses that solve real problems in Central Asia, and I believe inVision U's network and approach will give me the foundation to do that.\n\nQ: What's your biggest weakness?\nA: I can be overly competitive. Sometimes I focus too much on winning — debates, competitions, grades — and forget that collaboration might produce better outcomes than competition.\n\nQ: Tell us about a time you failed.\nA: My startup app idea won the school competition but when we tried to actually build it, we realized none of us had the technical skills. The project stalled. I learned that ideas without execution capability are worthless, which is why I've started learning basic programming.",
        "recommendation_summary": "Arman is a polished, ambitious student with strong organizational and communication skills. He excels in competitive academic environments and has demonstrated leadership in managing large-scale events."
    },
    {
        "id": "c-007",
        "name": "Zarina Ospanova",
        "age": 17,
        "application": {
            "education": {
                "school_type": "public",
                "gpa": 3.1,
                "academic_achievements": [],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Helping elderly grandmother with daily errands", "duration_months": 72, "role": "family helper"},
                {"activity": "Part-time work at grocery store", "duration_months": 24, "role": "cashier"}
            ],
            "projects": [
                {"name": "Interactive public transit accessibility map for Astana", "role": "creator", "impact": "Mapped 50+ bus stops and routes, data requested by city administration for repairs"}
            ],
            "languages": ["Kazakh", "Russian"],
            "skills": ["data collection", "problem-solving", "mapping", "perseverance"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "My grandmother lives on the outskirts of Astana. She is 74 and travels to the clinic on the other side of the city every week. It takes an hour and a half each way — two buses with a transfer, and not a single stop has a proper bench.\n\nOne winter she slipped on an icy bus stop and badly bruised her arm. That evening I looked at the city map with different eyes. I started noticing things I never saw before: high steps on buses, no shelters at stops, timetable signs that are impossible to read.\n\nI decided to map public transit convenience. For three months I rode routes, photographed stops, measured step heights, noted whether there were benches and shelters. I put it all on an interactive map and published it in city groups.\n\nThe reaction surprised me. Elderly people wrote that they now choose routes using my map. One woman wrote: 'Thank you for noticing us.' The city administration requested my data for planning stop repairs.\n\nMy grades aren't the highest. I study when I can — between shifts at the grocery store and helping my grandmother. But I think I understand something about the world that you can't read in a textbook. Leadership isn't loud speeches. It's paying attention to those who usually go unnoticed."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: I want to work on urban environments and make cities comfortable for everyone — not just the young and healthy. At inVision U I can learn to work with data and technology to scale what I've started.\n\nQ: What's your biggest weakness?\nA: I react too emotionally when I see injustice. Sometimes it prevents me from thinking strategically — I want to fix everything at once, but I need to prioritize.\n\nQ: Tell us about a time you failed.\nA: I tried to organize a meeting with city administration officials to discuss transport problems. I came prepared, with data and maps. But the official just said 'we'll take it into account' and nothing changed. I realized I need to change my approach — not just show problems, but propose specific solutions with budgets.",
        "recommendation_summary": "Zarina has a rare combination of empathy and practicality. Her transit accessibility mapping project shows maturity and systems thinking."
    },
    {
        "id": "c-008",
        "name": "Baurzhan Tulegenov",
        "age": 18,
        "application": {
            "education": {
                "school_type": "lyceum",
                "gpa": 3.7,
                "academic_achievements": [
                    "National Programming Contest - finalist",
                    "Regional Math Olympiad - 2nd place"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Coding club", "duration_months": 30, "role": "co-founder"},
                {"activity": "Open source contributions", "duration_months": 12, "role": "contributor"},
                {"activity": "Chess club", "duration_months": 48, "role": "member"}
            ],
            "projects": [
                {"name": "School schedule optimization app", "role": "developer", "impact": "Used by 400 students daily, reduced scheduling conflicts by 60%"},
                {"name": "Kazakh language learning chatbot", "role": "co-creator", "impact": "Prototype with 200 beta testers, helps Russian-speaking students learn Kazakh"}
            ],
            "languages": ["Russian", "Kazakh", "English", "Python"],
            "skills": ["programming", "algorithms", "machine learning basics", "problem decomposition"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "I write code, not speeches. Leadership always felt like something for the loud, charismatic people — the debate captains and student council presidents. I'm the person in the back of the room with headphones on.\n\nBut when I built the school schedule app, I accidentally became a leader. The app started as a personal project because I was frustrated with our terrible paper-based schedule system. I showed it to a few friends. They told friends. Within a week, half the school was using it and people were finding bugs faster than I could fix them.\n\nSuddenly I had 'users' who were angry when things broke. I had classmates volunteering to help. I needed to coordinate, prioritize, communicate updates. I needed to be a leader, even though I never intended to be one.\n\nThe hardest challenge was when a bug in the app caused 30 students to go to the wrong classroom. I got called to the principal's office. I was terrified and embarrassed. But instead of shutting the app down, I fixed the bug that night, wrote an honest post-mortem explaining what went wrong and how I fixed it, and shared it with all users.\n\nPeople respected the transparency. More volunteers joined after that. I learned that leadership in tech isn't about being perfect — it's about being honest when things break and fixing them fast.\n\nI also learned that building something people actually use is the most rewarding thing I've ever done. More than any olympiad medal."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: I want to build technology that matters for Kazakhstan. We have so many problems that good software could solve — education access, language preservation, government services. But most talented programmers here dream of leaving for Silicon Valley. I want to stay and build here.\n\nQ: What's your biggest weakness?\nA: I'm terrible at presenting and networking. I communicate much better through code and writing than in person. I get nervous speaking in front of groups.\n\nQ: Tell us about a time you failed.\nA: The Kazakh chatbot was supposed to launch last month but the NLP model quality wasn't good enough. The grammar correction feature was giving wrong suggestions 30% of the time. I decided to delay the launch rather than release something broken. Some team members were frustrated but I believe shipping a bad product is worse than shipping late.",
        "recommendation_summary": "Baurzhan is a gifted programmer with a builder's mindset. His projects demonstrate both technical skill and genuine desire to solve real problems. He leads through competence and integrity rather than charisma."
    },
    {
        "id": "c-009",
        "name": "Madina Alieva",
        "age": 17,
        "application": {
            "education": {
                "school_type": "gymnasium",
                "gpa": 3.55,
                "academic_achievements": [
                    "City-level essay competition - 2nd place",
                    "School Environmental Award"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Environmental club", "duration_months": 24, "role": "leader"},
                {"activity": "School theater", "duration_months": 36, "role": "actress and playwright"},
                {"activity": "Blogging about sustainability", "duration_months": 18, "role": "writer"}
            ],
            "projects": [
                {"name": "Eco-theater: environmental plays for elementary schools", "role": "creator and director", "impact": "Performed in 8 schools, reaching 500+ young students with environmental messages"}
            ],
            "languages": ["Russian", "Kazakh", "English"],
            "skills": ["creative writing", "theater", "environmental science", "storytelling"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "Nobody wants to listen to a lecture about recycling. Trust me, I tried. I gave a presentation at a school assembly about plastic pollution and watched 200 students check their phones simultaneously. It was humiliating.\n\nBut I couldn't let it go. The environmental crisis is the defining challenge of our generation, and I felt a responsibility to make people care. So I asked myself: what do people actually pay attention to? Stories. Drama. Emotion.\n\nI combined my two passions — theater and environmentalism — and created 'Eco-Theater.' I wrote short plays where the characters are dealing with environmental problems in relatable ways. A family arguing about water usage. A student discovering their favorite snack brand is destroying forests. A future where Astana is underwater.\n\nThe first play was rough. My acting friends thought environmental topics were 'boring' and I had to convince them one by one. The first school we performed at was skeptical — their teachers expected a boring educational program. But when the kids were crying during the flooding scene and laughing during the recycling comedy sketch, everyone understood.\n\nWe've now performed in 8 schools. Elementary kids go home and tell their parents to recycle. One principal told me our play did more for environmental awareness than a year of their curriculum.\n\nLeadership, I learned, is about translation. Taking something important that people tune out and finding the frequency they're actually listening on. Facts didn't work. Stories did."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: Climate change is going to hit Central Asia hard — water scarcity, extreme heat, agricultural collapse. I want to work on environmental solutions but I realize that technology and policy matter as much as awareness. inVision U can give me the skills to work on these problems from multiple angles.\n\nQ: What's your biggest weakness?\nA: I can be idealistic to the point of being impractical. I sometimes pursue ideas that excite me creatively without considering whether they're feasible or scalable.\n\nQ: Tell us about a time you failed.\nA: I tried to start a school composting program. It was a mess — literally. We didn't have proper containers, it smelled terrible, and the janitor threatened to quit. I learned that enthusiasm without practical planning leads to disaster. The eco-theater works because I plan meticulously now.",
        "recommendation_summary": "Madina has a unique ability to combine creativity with purpose. Her eco-theater project is innovative and effective. She's a passionate communicator who finds unconventional solutions to reach people."
    },
    {
        "id": "c-010",
        "name": "Ruslan Ibragimov",
        "age": 18,
        "application": {
            "education": {
                "school_type": "private",
                "gpa": 3.8,
                "academic_achievements": [
                    "National English Olympiad - 1st place",
                    "Regional Debate Championship - winner",
                    "Published article in youth magazine"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Debate team", "duration_months": 36, "role": "captain"},
                {"activity": "Youth journalism club", "duration_months": 24, "role": "editor-in-chief"},
                {"activity": "Volunteer English teacher for migrant children", "duration_months": 12, "role": "teacher"}
            ],
            "projects": [
                {"name": "Online youth news platform", "role": "co-founder", "impact": "Published 150+ articles, 5000 monthly readers, covering youth issues in Kazakhstan"}
            ],
            "languages": ["Russian", "English", "Kazakh", "French"],
            "skills": ["journalism", "debate", "English", "critical thinking", "media literacy"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "When I started our youth news platform, I thought journalism was about writing good articles. I was wrong. It's about building trust, managing people, and making hard editorial decisions.\n\nThe biggest challenge came when one of our reporters wrote an article criticizing the school administration's handling of bullying. The article was well-researched and important. But the school principal called me and said if we published it, our journalism club would lose its room and funding.\n\nI was terrified. The easy path was to kill the article. Most of my team wanted to. But the reporter had spent weeks on it, and the bullying victims she interviewed trusted us to tell their story.\n\nI negotiated a compromise: we published the article but gave the administration space to respond in the same issue. We presented both sides fairly. The principal was still unhappy, but we kept our room. More importantly, the article led to a new anti-bullying policy at school.\n\nThis taught me that leadership often means standing in the uncomfortable middle ground. It's not about being fearless — I was scared the entire time. It's about finding a path that honors your principles without being reckless. And it's about protecting the people who trusted you, even when it would be easier not to.\n\nRunning the platform also taught me about managing a team of volunteers — people who can leave anytime. You can't command them. You have to inspire them and make the work meaningful enough that they choose to stay."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: Information is power, and Kazakhstan needs independent, quality journalism. inVision U's focus on leadership and social impact aligns with my goal of building media that serves the public interest. I also want to learn about the business side — how to make independent media sustainable.\n\nQ: What's your biggest weakness?\nA: I can be too diplomatic sometimes, trying to please everyone. In journalism, sometimes you need to take a clear stand, and I struggle with that when it might upset people I respect.\n\nQ: Tell us about a time you failed.\nA: Early on, our platform published an article that turned out to have factual errors. We hadn't fact-checked rigorously enough. We published a correction and I implemented a mandatory fact-checking process. It slowed our output but improved our credibility enormously.",
        "recommendation_summary": "Ruslan combines intellectual sharpness with ethical maturity. His navigation of the editorial dilemma showed leadership wisdom rare in someone his age. He's an excellent communicator who cares deeply about truth and fairness."
    },
    {
        "id": "c-011",
        "name": "Dinara Suleimenova",
        "age": 17,
        "application": {
            "education": {
                "school_type": "public",
                "gpa": 2.9,
                "academic_achievements": [],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Social media content creation", "duration_months": 12, "role": "creator"}
            ],
            "projects": [],
            "languages": ["Kazakh", "Russian"],
            "skills": ["social media", "video editing"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "I want to go to inVision U because it is a great university with amazing opportunities. I have always been a leader in my school and community. My biggest challenge was when I had to organize a school event and everything went wrong but I persevered and it turned out great in the end.\n\nI believe that leadership means being a good communicator and working hard. I always try my best and never give up. I am passionate about making the world a better place and I think inVision U can help me achieve my goals.\n\nI am a quick learner and I work well in teams. I have experience in social media which I think is very important in today's world. I want to use my skills to help others and create positive change.\n\nThank you for considering my application. I would be honored to attend inVision U and I promise to work hard and make the most of this opportunity."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: It's a really good university and the scholarship would help my family a lot.\n\nQ: What's your biggest weakness?\nA: I don't really have any big weaknesses. Maybe I work too hard sometimes.\n\nQ: Tell us about a time you failed.\nA: I can't think of a specific time. I usually figure things out.",
        "recommendation_summary": "Dinara is a pleasant student. She could benefit from more academic focus and clearer goals."
    },
    {
        "id": "c-012",
        "name": "Talgat Nurpeissov",
        "age": 18,
        "application": {
            "education": {
                "school_type": "public",
                "gpa": 3.3,
                "academic_achievements": [
                    "Regional agriculture competition - participant"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Family farm work", "duration_months": 60, "role": "worker"},
                {"activity": "Village youth group", "duration_months": 18, "role": "organizer"}
            ],
            "projects": [
                {"name": "Drip irrigation system from recycled materials", "role": "designer and builder", "impact": "Increased family crop yield by 25%, system copied by 4 neighboring farms"},
                {"name": "Agricultural knowledge-sharing WhatsApp group", "role": "moderator", "impact": "120 members from rural communities sharing farming tips and market prices"}
            ],
            "languages": ["Kazakh", "Russian"],
            "skills": ["agriculture", "practical engineering", "community networking"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "I grew up on a farm in Kyzylorda region. When people hear 'farm' they think of something simple. It's not. Farming is constant problem-solving — weather, water, pests, prices. You fight nature and the market at the same time.\n\nTwo years ago our region had the worst drought in a decade. Our crops were dying. My father was ready to accept the loss, like everyone else. But I'd been reading about drip irrigation on my phone — simple systems that use much less water than flood irrigation. The problem was we couldn't afford a real system.\n\nSo I built one from plastic bottles, old hoses, and valves I found at a scrap yard. My father thought I was wasting time. Our neighbors literally laughed. The first version leaked everywhere. The second version clogged. The third version worked.\n\nWe saved 70% of our tomato crop while neighbors lost almost everything. When they saw our results, the laughing stopped. Four families asked me to help them build the same system. I spent the rest of that summer going farm to farm, teaching the technique.\n\nThat experience taught me two things about leadership. First, sometimes the leader is the person who reads the most. I found the solution on the internet — information that was available to everyone but that nobody else was looking for. Second, leadership in a rural community works through demonstration, not persuasion. Nobody believed in drip irrigation until they saw our tomatoes.\n\nI started a WhatsApp group where farmers in our region share what works. Old men who've farmed for 40 years now ask me about new techniques. It's strange and beautiful.\n\nI know I'm from a village and my English is basic and my school isn't famous. But I know how to grow things — plants and ideas."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: Agriculture feeds everyone but farmers are poor and ignored. I want to learn technology and business so I can come back and modernize farming in my region. Not with expensive Western solutions but with smart, affordable ones that real farmers can use.\n\nQ: What's your biggest weakness?\nA: My education has gaps. Village school doesn't compare to city schools. My English is poor. I worry I won't be able to keep up academically.\n\nQ: Tell us about a time you failed.\nA: I tried to convince our village administration to invest in a community greenhouse. They said there was no budget. I was frustrated and gave up too quickly. Looking back, I should have tried to find alternative funding or built a small prototype first to prove the concept, like I did with irrigation.",
        "recommendation_summary": "Talgat has extraordinary practical intelligence and initiative for someone from his background. His irrigation innovation and knowledge-sharing network show genuine leadership — the kind that comes from necessity, not privilege. His academic preparation has gaps but his potential is enormous."
    },
    {
        "id": "c-013",
        "name": "Aliya Karimova",
        "age": 17,
        "application": {
            "education": {
                "school_type": "private",
                "gpa": 3.92,
                "academic_achievements": [
                    "National Chemistry Olympiad - 2nd place",
                    "International Math Competition - bronze medal",
                    "Full marks on SAT Math section",
                    "Published research paper (co-author) on water quality"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Science research club", "duration_months": 24, "role": "president"},
                {"activity": "Volunteer at animal shelter", "duration_months": 6, "role": "volunteer"},
                {"activity": "Photography club", "duration_months": 12, "role": "member"}
            ],
            "projects": [
                {"name": "Water quality testing in Almaty rivers", "role": "lead researcher", "impact": "Tested 15 sites, findings presented to city environmental department"}
            ],
            "languages": ["Russian", "English", "Kazakh", "Korean"],
            "skills": ["chemistry", "research", "data analysis", "scientific writing"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "The intersection of scientific inquiry and leadership presents a fascinating paradigm through which we can examine the multifaceted nature of personal growth and development. My experience conducting water quality research in Almaty's river systems served as a catalyst for understanding the complexities inherent in leading a scientific team.\n\nThe primary challenge I encountered was navigating the intricate dynamics of collaborative research while maintaining rigorous scientific standards. As the lead researcher, I was responsible for coordinating sample collection across 15 sites, ensuring methodological consistency, and synthesizing findings into a coherent narrative that would be accessible to both scientific and public audiences.\n\nThis endeavor required me to develop sophisticated communication strategies that could bridge the gap between technical expertise and stakeholder engagement. I facilitated weekly team meetings where we employed evidence-based decision-making frameworks to address methodological challenges and optimize our research protocols.\n\nThe culmination of our efforts was a comprehensive presentation to the city environmental department, where I articulated our findings with clarity and conviction. The positive reception from municipal authorities validated our approach and demonstrated the tangible impact that student-led research can have on policy discussions.\n\nThrough this experience, I cultivated essential leadership competencies including strategic planning, stakeholder management, and the ability to translate complex scientific concepts into actionable recommendations. These skills have profoundly shaped my understanding of how scientific leadership can drive meaningful societal change and environmental stewardship.\n\nI am confident that the analytical rigor and leadership acumen I have developed through this experience will enable me to make significant contributions to the inVision U community and beyond."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: I want to pursue environmental science research at a higher level. inVision U's interdisciplinary approach appeals to me because environmental problems require solutions that combine science, policy, and technology.\n\nQ: What's your biggest weakness?\nA: I tend to overthink things and spend too much time planning before acting. I've been working on finding the right balance between preparation and execution.\n\nQ: Tell us about a time you failed.\nA: Our initial water sampling methodology had contamination issues that invalidated two weeks of data. It was a significant setback. I revised our protocols based on published best practices and implemented quality control checks at each stage.",
        "recommendation_summary": "Aliya is an outstanding student with exceptional academic credentials and genuine research experience. She is methodical, intelligent, and capable of producing work at a level beyond her years."
    },
    {
        "id": "c-014",
        "name": "Yerlan Smagul",
        "age": 18,
        "application": {
            "education": {
                "school_type": "gymnasium",
                "gpa": 3.45,
                "academic_achievements": [
                    "City chess championship - 1st place",
                    "School coding competition - winner"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Chess (competitive)", "duration_months": 72, "role": "regional champion"},
                {"activity": "Peer tutoring (math and physics)", "duration_months": 18, "role": "tutor"},
                {"activity": "App development (self-taught)", "duration_months": 24, "role": "developer"}
            ],
            "projects": [
                {"name": "Offline study app for ЕНТ exam prep", "role": "developer", "impact": "Used by students in 4+ schools, especially in areas with unreliable internet"},
                {"name": "Chess teaching program for community center children", "role": "volunteer teacher", "impact": "Weekly sessions for 15+ children over 8 months"}
            ],
            "languages": ["Kazakh", "Russian", "English"],
            "skills": ["programming", "chess strategy", "mentoring", "app development"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "Last summer our town's internet went down for three days. It sounds minor, but for students preparing for ЕНТ exams it was a disaster — all the practice tests and study materials were online. Kids were panicking in group chats, asking who had textbooks they could borrow.\n\nI'm a programmer. I can't fix the internet, but I can build something that works without it. Over that weekend I built an offline study app — basically a collection of past exam questions, formulas, and explanations packaged into an Android app that runs without any connection. The hard part wasn't the code. It was collecting the content. I spent two days going through every math and physics resource I could find, organizing them by topic, checking the answers.\n\nI shared it in our school group chat on Monday. By Wednesday it had spread to three other schools. A teacher I'd never met messaged me saying her students in a village with unreliable internet had been using it daily.\n\nThat's when I understood something about building tools — you don't always know who needs them most. I built it for my classmates during an outage. But the real users were kids in places where the internet is always unreliable.\n\nI also teach chess at an community center every Saturday. It started because I wanted to give back, but it became something deeper. Chess teaches children that their decisions matter — that thinking ahead leads to better outcomes. For kids who often feel powerless, that's a powerful idea.\n\nI don't think of myself as a leader. I think of myself as someone who notices gaps and fills them with code or with time."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: I want to build technology that solves real problems for people in Central Asia. The offline study app showed me that there's a huge gap between what tech can do and what's available in our region. I need to learn how to think bigger and build things that scale beyond my school group chat.\n\nQ: What's your biggest weakness?\nA: I get too absorbed in building and forget to ask people what they actually need. My first version of the study app had features nobody used because I assumed what would be useful instead of asking. I've learned to talk to users first, but it's still my instinct to just start coding.\n\nQ: Tell us about a time you failed.\nA: I tried to organize a coding bootcamp for younger students at my school. Only four kids showed up, and two left after the first session because I was teaching too fast. I was basically lecturing at them instead of letting them build things. The third session I scrapped my plan and just gave them a simple game to modify. That worked much better. I learned that teaching isn't about showing what you know — it's about meeting people where they are.",
        "recommendation_summary": "Yerlan combines technical skill with practical problem-solving. His offline study app project shows initiative and awareness of real community needs. His chess teaching at the community center demonstrates consistent, quiet commitment to helping others."
    },
    {
        "id": "c-015",
        "name": "Saule Baimenova",
        "age": 17,
        "application": {
            "education": {
                "school_type": "lyceum",
                "gpa": 3.75,
                "academic_achievements": [
                    "Regional Biology Olympiad - 3rd place",
                    "National Volunteer Award nominee"
                ],
                "years_of_study": 11
            },
            "extracurriculars": [
                {"activity": "Red Crescent Youth volunteer", "duration_months": 30, "role": "team coordinator"},
                {"activity": "First aid instructor (certified)", "duration_months": 18, "role": "instructor"},
                {"activity": "School health awareness club", "duration_months": 24, "role": "founder"}
            ],
            "projects": [
                {"name": "First aid training for rural schools", "role": "project lead", "impact": "Trained 200+ students and 30 teachers in basic first aid across 8 rural schools"},
                {"name": "Health literacy campaign on social media", "role": "creator", "impact": "TikTok series on first aid basics, 50K+ total views"}
            ],
            "languages": ["Kazakh", "Russian", "English"],
            "skills": ["first aid", "health education", "volunteer management", "public health communication"]
        },
        "essay": {
            "prompt": "Describe a challenge you overcame and what it taught you about leadership.",
            "text": "A boy in my village choked on food at a birthday party two years ago. Thirty adults stood around panicking. Nobody knew what to do. By luck, someone's uncle who was a retired paramedic was there and performed the Heimlich maneuver. The boy survived. But the image of a room full of adults frozen by helplessness haunted me.\n\nThe next week I signed up for Red Crescent first aid training. After getting certified, I asked a simple question: why isn't basic first aid taught in every school? The answer was always the same — 'no time in the curriculum,' 'no budget,' 'not a priority.'\n\nSo I made it happen outside the curriculum. I organized weekend first aid workshops in schools, starting with my own. The first challenge was convincing principals that 16-year-old me was qualified to teach their students. I brought my certification, a detailed lesson plan, and did a demo session. The demo worked — kids were excited, teachers were impressed.\n\nThe real challenge was the rural schools. Transportation, equipment, and trust. Rural communities don't easily trust a teenager from the city telling them what to do. I learned to partner with local health workers who vouched for the program. I trained local teachers so the knowledge would stay after I left.\n\nTwo months ago, a teacher I trained performed CPR on a colleague who collapsed during a staff meeting. The colleague survived. That teacher sent me a voice message crying, saying 'you taught me how to save a life.'\n\nI learned that leadership is about building capacity in others, not creating dependency on yourself. The goal isn't for me to be everywhere — it's for everyone to know what to do when it matters."
        },
        "interview_transcript": "Q: Why do you want to attend inVision U?\nA: Public health in Kazakhstan has gaps that I want to help close. inVision U's emphasis on building practical solutions for real problems resonates with me. I want to learn how to create health education programs that can scale nationally.\n\nQ: What's your biggest weakness?\nA: I sometimes underestimate how long things take. I'll commit to training sessions in three schools in one weekend and then realize I can't physically be in three places. I'm learning to plan more realistically.\n\nQ: Tell us about a time you failed.\nA: My first TikTok health video was scientifically accurate but completely boring. It got 47 views. I studied what makes health content engaging on social media and completely changed my approach — shorter, more visual, using humor. The next video got 12,000 views. I learned that expertise means nothing if you can't make people watch.",
        "recommendation_summary": "Saule is driven by genuine concern for public safety. Her first aid training program has measurable real-world impact — it literally saved a life. She's practical, organized, and knows how to work within communities rather than imposing solutions from outside."
    }
]

def main():
    output_path = os.path.join(os.path.dirname(__file__), "candidates.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(CANDIDATES, f, ensure_ascii=False, indent=2)
    print(f"Generated {len(CANDIDATES)} candidates → {output_path}")


if __name__ == "__main__":
    main()
