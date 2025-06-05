from calls_parser import CallGraphBuilder
import os

# print(os.listdir('../../..'))

# sources:
# https://github.com/testdouble/java-testing-example
# https://github.com/KrllF/metrics_for_autodocumentation#
# https://github.com/tired-racoon/sentiment_analysis_service
# https://github.com/spring-petclinic/spring-petclinic-kotlin


# just for test

# java: java-testing-example
# python: sentiment_analysis_service
# go: metrics_for_autodocumentation
# kotlin: spring-petclinic-kotlin

builder = CallGraphBuilder(repo_path="../../../sentiment_analysis_service")
builder.build_from_repo()
call_graph = builder.get_call_graph()

for func, info in call_graph.items():
    print(f"{func} calls: {info['calls']} | called by: {info['called_by']}")
    try:
        print(info["location"])
    except:
        print(f"Function {func} is undifined!")
