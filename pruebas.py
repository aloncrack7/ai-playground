from agents.orchestrator_agent import Orchestrator

agent = Orchestrator()

text = input()
print(agent.run(text))