import gradio as gr

def hello(name):
    return f"Hello, {name}!"

demo = gr.Interface(
    fn=hello,
    inputs="text",
    outputs="text",
    title="Simple Gradio Test"
)

if __name__ == "__main__":
    demo.launch(server_name="localhost", server_port=7867)
