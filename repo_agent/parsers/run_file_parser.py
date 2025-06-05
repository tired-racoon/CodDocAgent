from file_parser import TreeSitterParser


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


# examples:
# ../../../sentiment_analysis_service/bot.py
# ../../../java-testing-example/example/src/main/java/example/FeedsWalrus.java
# ../../../metrics_for_autodocumentation/internal/app/app.go
# ../../../spring-petclinic-kotlin/src/main/kotlin/org/springframework/samples/petclinic/owner/Owner.kt


parser = TreeSitterParser(language_name="kotlin")
structure = parser.generate_file_structure(
    "../../../spring-petclinic-kotlin/src/main/kotlin/org/springframework/samples/petclinic/owner/Owner.kt"
)

from pprint import pprint

pprint(structure)
