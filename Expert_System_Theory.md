NED UNIVERSITY OF ENGINEERING AND TECHNOLOGY  
Muhammad Wasiq Noor

- An expert system is a computer program designed to simulate the decision-making abilities of a human expert in a specific domain. It applies reasoning capabilities to reach conclusions and can often provide explanations for its decisions.
- Expert systems are part of the broader field of artificial intelligence, specifically under the umbrella of knowledge-based systems. They rely on a knowledge base (a collection of facts and rules) and an inference engine (the logic system that applies the rules to the knowledge base to derive conclusions).

## WHAT IS AN EXPERT SYSTEM?

## PRIMARY OBJECTIVES

The main goal of an expert system is to emulate the decisionmaking process of a human expert. This involves diagnosing issues, providing advice, or solving complex problems that require specialized knowledge.

Expert systems are designed to be accessible, allowing nonexperts to benefit from expert-level decision-making without requiring in-depth knowledge of the domain.

## CORE FUNCTIONS

- Decision Support: Expert systems assist in making informed decisions by evaluating available data against a set of predefined rules.
- Automation of Expert Knowledge: They encapsulate the expertise of human professionals, enabling consistent and repeatable decision-making.
- Training and Education: Expert systems can be used as educational tools to train individuals in specific domains by simulating problem-solving scenarios.

## COMPONENTS OF EXPERT SYSTEMS

### 01 Knowledge Base

**Definition and Structure:**

- The knowledge base is the core component of an expert system, containing domain-specific information such as facts, heuristics, and rules. This knowledge can be captured in various forms, including rules, frames, and objects.
- Example: In a medical expert system, the knowledge base might include facts about diseases, symptoms, diagnostic criteria, and treatment protocols.

**Types of Knowledge:**

- Declarative Knowledge: Facts and information about the domain, such as specific symptoms of a disease or properties of materials in an engineering application.
- Procedural Knowledge: This involves the procedures or rules for problem-solving within the domain, such as the steps to diagnose an illness based on symptoms.

## COMPONENTS OF EXPERT SYSTEMS

### 02 Inference Engine

**Role and Functionality:**

- The inference engine is responsible for applying logical rules to the knowledge base to derive new information or reach conclusions. It simulates the reasoning process of a human expert.
- Forward Chaining: A reasoning approach that starts with known facts and applies rules to extract more facts until a goal is reached.
- Backward Chaining: This approach starts with a goal and works backward to determine if there is evidence to support the goal by checking the relevant facts.

**Examples of Inference Techniques:**

- Rule-Based Inference: Utilizes if-then rules to generate conclusions.
- Case-Based Reasoning: Involves comparing new problems to past cases stored in the knowledge base to find the most similar case and applying its solution.

## COMPONENTS OF EXPERT SYSTEMS

### 03 User Interface

**Design and Interaction:**

The user interface allows users to interact with the expert system, inputting data, querying the system, and receiving advice or solutions. A well-designed interface is crucial for ensuring that non-expert users can easily access the system’s capabilities.

**Example:**

In a financial expert system, the user interface might allow a user to input various financial metrics and receive investment advice.

## COMPONENTS OF EXPERT SYSTEMS

### 04 Explanation Facility

**Importance of Transparency:**

Expert systems often include an explanation facility that provides users with justifications or explanations for the decisions made by the system. This is crucial for building user trust and understanding.

**Example:**

After diagnosing a condition, a medical expert system might explain why a particular diagnosis was made based on the symptoms and rules applied.

## COMPONENTS OF EXPERT SYSTEMS

### 05 Knowledge Acquisition Module

**Automating Knowledge Acquisition:**

This module helps in the continuous updating and refinement of the knowledge base. It can involve automated processes that learn from new data or inputs from human experts.

**Example:**

A knowledge acquisition module in a legal expert system might automatically incorporate new legal precedents and rulings into the system.

## Real-World Applications of Expert Systems

### Medical Diagnosis Systems

**Functionality and Impact:**

- Expert systems in medicine are used to assist doctors in diagnosing diseases, suggesting treatments, and predicting patient outcomes. These systems can analyze complex medical data and offer diagnostic recommendations based on established medical knowledge.
- Example: MYCIN, an early expert system, was designed to diagnose bacterial infections and recommend antibiotic treatments. It utilized a rule-based approach to determine the best course of action based on patient symptoms and laboratory results.

## Real-World Applications of Expert Systems

### Financial Decision-Making

**Use Cases in Finance:**

- In finance, expert systems are employed to guide investment decisions, assess credit risk, and manage portfolios. These systems can process large amounts of financial data and identify patterns that inform investment strategies.
- Example: An expert system might analyze stock market trends and advise investors on the best times to buy or sell assets, taking into account risk factors and historical data.

## Real-World Applications of Expert Systems

### Industrial Process Control

**Enhancing Efficiency and Safety:**

- Expert systems in industrial settings monitor and control complex processes such as manufacturing, chemical processing, and power generation. These systems ensure optimal performance and can quickly respond to abnormalities or emergencies.
- Example: In a power plant, an expert system might continuously monitor various parameters such as temperature, pressure, and flow rates, automatically adjusting controls to maintain safe and efficient operations.

## Real-World Applications of Expert Systems

### Legal Expert Systems

**Supporting Legal Decision-Making:**

- Legal expert systems assist in legal research, case analysis, and the drafting of legal documents. These systems can analyze legal texts, identify relevant precedents, and suggest legal strategies.
- Example: A legal expert system might help lawyers determine the likely outcome of a case by comparing it to similar past cases and the rulings associated with them.

## Real-World Applications of Expert Systems

### Agricultural Management

**Optimizing Crop Production:**

- In agriculture, expert systems are used to optimize crop production by analyzing soil conditions, weather patterns, and plant health. They can suggest planting schedules, pest control measures, and irrigation strategies.
- Example: An expert system in agriculture might advise farmers on the best times to plant crops based on soil moisture levels, expected rainfall, and historical yield data.

## THANK YOU

M U H A M M A D W A S I Q N O O R

---

Muhammad Wasiq Noor  
NED University of Engineering and Technology

## Components of Expert Systems

**Knowledge Base as the System's Foundation:**

The knowledge base is the foundation of an expert system, housing the domain-specific knowledge that the system uses to make decisions. The quality and comprehensiveness of this knowledge directly affect the system's accuracy and reliability.

**Inference Engine as the Decision-Making Core:**

The inference engine is the system's brain, applying logical rules to the knowledge base to derive conclusions or make decisions. Its efficiency determines how well the system can emulate human reasoning.

**User Interface as the Interaction Point:**

The user interface is the system's front-end, allowing users to interact with the expert system. A well-designed interface ensures that users can easily input data, query the system, and understand the system's outputs.

**Definition and Role:**

The knowledge base is a repository of facts, rules, and heuristics relevant to a particular domain. It contains both declarative knowledge (facts and information) and procedural knowledge (rules and instructions for problemsolving).

**Types of Knowledge Stored:**

Facts: Fundamental truths about the domain, such as patient symptoms in a medical expert system or financial metrics in an investment system.

Rules: Conditional statements that describe the relationships between different pieces of knowledge. For example, "If a patient has a fever and a cough, then they may have the flu."

## KNOWLEDGE BASE

### Structure and Content

## KNOWLEDGE BASE

**Rule-Based Systems:**

Knowledge is represented in the form of "if-then" rules, which are straightforward and easy to understand. These rules are applied by the inference engine to draw conclusions based on the facts in the knowledge base.

**Semantic Networks and Frames:**

Semantic networks represent knowledge as a graph of interconnected nodes, where each node represents a concept, and the links between nodes represent relationships.

Frames are structured representations of stereotypical situations, consisting of slots and fillers. They provide a more flexible way to represent complex knowledge by encapsulating both declarative and procedural information.

### Methods of Knowledge Representation

## KNOWLEDGE BASE

**Methods for Building the Knowledge Base:**

Manual Entry: Knowledge is often entered manually by human experts, a process that requires close collaboration between domain experts and knowledge engineers.

Automated Learning: Machine learning techniques can be used to automatically populate and update the knowledge base by analyzing data and identifying patterns.

### Knowledge Acquisition

## KNOWLEDGE BASE

**Knowledge Bottleneck:**

One of the major challenges in expert systems is the "knowledge bottleneck, " where capturing and codifying expert knowledge is a slow and difficult process.

**Dynamic Knowledge:**

The knowledge base must be regularly updated to reflect new discoveries or changes in the domain. This requires a robust mechanism for knowledge acquisition and management.

### Challenges in Knowledge Management

**Core of Decision-Making:**

The inference engine applies logical rules to the knowledge base to derive new information or make decisions. It mimics the cognitive processes of a human expert, systematically working through potential solutions to a problem.

**Mechanisms of Inference:**

**Forward Chaining:**

This method starts with known facts and applies rules to infer new facts until a goal or solution is reached. It’s typically used in systems where the initial data is clear, but the outcome is unknown.

Example: A medical diagnostic system might use forward chaining to start with symptoms and apply rules to diagnose a disease.

## INFERENCE ENGINE

### Role and Function

**Mechanisms of Inference (contd.):**

**Backward Chaining:**

In backward chaining, the system starts with a hypothesis or goal and works backward to determine if there are enough supporting facts to confirm it. This is common in systems where the goal is known, but the necessary steps to achieve it are unclear.

Example: A legal expert system might start with a desired legal outcome and work backward to see if the facts of a case support it.

## INFERENCE ENGINE

### Role and Function

**Rule-Based Inference Engines:**

These engines use "if-then" rules to infer new knowledge. They are straightforward and easy to implement but may struggle with more complex or uncertain scenarios.

**Fuzzy Logic Inference Engines:**

Fuzzy logic allows for reasoning in situations where information is incomplete or ambiguous. It handles uncertainty by considering degrees of truth rather than binary true/false outcomes.

## INFERENCE ENGINE

### Types of Inference Engines

**Case-Based Reasoning:**

In case-based reasoning, the system compares new problems to previous cases stored in the knowledge base, applying solutions from similar cases to the current problem. This method is particularly useful in domains like law or medicine, where past cases are often used as precedents.

## INFERENCE ENGINE

### Types of Inference Engines

**Inference Efficiency:**

The efficiency of the inference engine is crucial for the system's performance. Techniques like pruning irrelevant rules and parallel processing can be used to optimize the decision-making process.

**Handling Complex Scenarios:**

The inference engine must be capable of handling complex scenarios where multiple rules interact or where contradictory information must be resolved.

## INFERENCE ENGINE

### Optimization and Efficiency

**Why Explanations Matter:**

Many expert systems include an explanation facility that allows users to understand the reasoning behind the system's conclusions. This is vital for user trust and for verifying the system's decisions.

**Types of Explanations:**

Trace Explanations: Show the sequence of rules applied and how the final conclusion was reached.

Justification Explanations: Provide the rationale behind why certain rules were applied, often including references to the knowledge base or external sources.

## INFERENCE ENGINE

### Explanation Facilities

**Importance of Usability:**

The user interface (UI) is how users interact with the expert system, making usability a critical factor. A well-designed UI ensures that users can easily input data, understand system outputs, and navigate the system’s features.

**Interaction Models:**

**Text-Based Interfaces:**

Traditional expert systems often use text-based interfaces where users input data in textual form and receive text-based responses. While simple, these interfaces can be cumbersome for non-expert users.

## USER INTERFACE

### Design Principles

**Interaction Models:**

**Graphical User Interfaces (GUIs):**

Modern expert systems often employ GUIs, which provide a more intuitive way to interact with the system. Users can click on icons, select options from menus, and view outputs in a more visually appealing format.

**Natural Language Interfaces:**

Some expert systems incorporate natural language processing (NLP) to allow users to interact with the system using everyday language. This approach can make the system more accessible, particularly for nontechnical users.

## USER INTERFACE

### Design Principles

**Interactive Feedback:**

The UI should provide real-time feedback to users, such as confirming data inputs, showing progress on complex tasks, and explaining any errors or issues encountered.

**Customization and Adaptability:**

The interface should be customizable to suit the needs of different users. For example, an expert user might prefer detailed technical feedback, while a novice user might need simpler, more guided interactions.

## USER INTERFACE

### Feedback Mechanisms

**Medical Expert System Interface:**

In a medical expert system, the UI might allow doctors to input symptoms through dropdown menus, view diagnostic suggestions, and see detailed explanations of the system’s reasoning, all within an easy-to-navigate interface.

**Financial Expert System Interface:**

A financial expert system might feature a dashboard where users can input financial metrics, run simulations, and view visualizations of potential investment outcomes.

## USER INTERFACE

### Case Studies of User Interface Design

## Integrating Expert Systems with Other Technologies

**Hybrid Systems:**

Expert systems are often integrated with other AI technologies, such as machine learning algorithms, to enhance their capabilities. For instance, machine learning can be used to update the knowledge base or optimize the inference engine.

**Future Trends:**

The future of expert systems lies in their integration with advanced analytics, big data, and real-time processing capabilities, allowing them to handle more complex scenarios and provide even more accurate and timely advice.

## Thank You

Muhammad Wasiq Noor

---

Muhammad Wasiq Noor  
NED UNIVERSITY OF ENGINEERING AND TECHNOLOGY

Knowledge Acquisition: Gather domain-specific knowledge from human experts, literature, and other resources. This includes identifying key facts, rules, and decision-making processes used by experts.

## Problem Identification

Understanding the Domain: Clearly define the problem the expert system is intended to solve. For example, diagnosing diseases, recommending financial investments, or troubleshooting technical issues.

Encoding the Knowledge: Use a programming language or expert system shell to encode the knowledge base. This involves converting the rules and facts into code that can be processed by the inference engine.

## Knowledge Representation

Creating the Knowledge Base: Organize the acquired knowledge into a structured form, often using rules, facts, and if-then statements.

Example: If a patient has a fever and a sore throat, then they may have strep throat.

Control Strategies: Implement strategies for selecting and applying rules, such as conflict resolution (e.g., prioritizing certain rules over others).

## Designing the Inference Engine

Forward Chaining vs. Backward Chaining:

Forward Chaining: Start with known facts and apply rules to derive new facts or reach conclusions.

Backward Chaining: Start with a goal (e.g., a diagnosis) and work backward to see if there are facts that support this goal.

Interactive Interface: Design an interface that allows users to input data and receive explanations for the system’s decisions.

Example: A chatbot interface where users input symptoms and receive a diagnosis.

## User Interface Design

Selecting a Programming Language: Choose a suitable language, such as Python, PROLOG, or a dedicated expert system shell.

## Coding the Expert System

Selecting a Programming Language: Choose a suitable language, such as Python, PROLOG, or a dedicated expert system shell.

Reliability: Assess the system’s ability to consistently provide accurate results over time.

## Evaluating System Performance

Accuracy: Measure how often the expert system makes correct diagnoses or decisions.

Improving the System: Use feedback to refine the knowledge base, inference engine, and user interface.

## User Feedback

Collecting Feedback: Ask users to provide feedback on the system’s usability, accuracy, and helpfulness.

## Thank You!

Muhammad Wasiq Noor