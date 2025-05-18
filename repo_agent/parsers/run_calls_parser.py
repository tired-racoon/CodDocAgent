from calls_parser import CallGraphBuilder
import os
# print(os.listdir('../../..'))

# just for test
builder = CallGraphBuilder(repo_path="../../../sentiment_analysis_service")
builder.build_from_repo()
call_graph = builder.get_call_graph()

for func, info in call_graph.items():
    print(f"{func} calls: {info['calls']} | called by: {info['called_by']}")
