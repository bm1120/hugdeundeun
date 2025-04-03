from langgraph.graph import StateGraph, START, END
from .nodes import download_image, describe_image, check_image_description
from .edges import decide_to_generate, decide_to_regenerate
from .models import GraphState

# Define a new graph
workflow = StateGraph(GraphState)

# Define the nodes we will cycle between
workflow.add_node("download_image", download_image)
workflow.add_node("describe_image", describe_image)
workflow.add_node("check_image_description", check_image_description)

# Add edges
workflow.add_edge(START, "download_image")

workflow.add_conditional_edges(
    "download_image",
    decide_to_generate,
    {
        "end": END,
        "generate": "describe_image"
    }
)

workflow.add_edge("describe_image", "check_image_description")

workflow.add_conditional_edges(
    "check_image_description",
    decide_to_regenerate,
    {
        "nextstep": END,
        "regenerate": "describe_image",
        "end": END
    }
)

# Compile
graph = workflow.compile()