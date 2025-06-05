import gradio as gr
import markdown

from repo_agent.log import logger


class GradioInterface:
    def __init__(self, respond_function):
        self.respond = respond_function
        self.cssa = """
                <style>
                        .outer-box {
                            border: 1px solid #333;
                            border-radius: 10px;
                            padding: 10px;
                        }

                        .title {
                            margin-bottom: 10px;
                        }

                        .inner-box {
                            border: 1px solid #555;
                            border-radius: 5px;
                            padding: 10px;
                        }

                        .content {
                            white-space: pre-wrap;
                            font-size: 16px;
                            height: 405px;
                            overflow: auto;
                        }
                    </style>
                    <div class="outer-box"">
        
        """
        self.cssb = """
                        </div>
                    </div>
                </div>
        """
        self.setup_gradio_interface()

    def wrapper_respond(self, msg_input, system_input):
        msg, output1, output2, output3, code, codex = self.respond(
            msg_input, system_input
        )
        output1 = markdown.markdown(str(output1))
        output2 = markdown.markdown(str(output2))
        code = markdown.markdown(str(code))
        output1 = (
            self.cssa
            + """
                          <div class="title">Response</div>
                            <div class="inner-box">
                                <div class="content">
                """
            + str(output1)
            + """
                        </div>
                    </div>
                </div>
                """
        )
        output2 = (
            self.cssa
            + """
                          <div class="title">Embedding Recall</div>
                            <div class="inner-box">
                                <div class="content">
                """
            + str(output2)
            + self.cssb
        )
        code = (
            self.cssa
            + """
                          <div class="title">Code</div>
                            <div class="inner-box">
                                <div class="content">
                """
            + str(code)
            + self.cssb
        )

        return msg, output1, output2, output3, code, codex

    def clean(self):
        msg = ""
        output1 = gr.HTML(
            self.cssa
            + """
                                        <div class="title">Response</div>
                                            <div class="inner-box">
                                                <div class="content">
                      
                                            """
            + self.cssb
        )
        output2 = gr.HTML(
            self.cssa
            + """
                                        <div class="title">Embedding Recall</div>
                                            <div class="inner-box">
                                                <div class="content">
                                    
                                            """
            + self.cssb
        )
        output3 = ""
        code = gr.HTML(
            self.cssa
            + """
                                        <div class="title">Code</div>
                                            <div class="inner-box">
                                                <div class="content">
                                   
                                            """
            + self.cssb
        )
        codex = ""
        return msg, output1, output2, output3, code, codex

    def setup_gradio_interface(self):
        with gr.Blocks() as demo:
            gr.Markdown(
                """
                # RepoAgent: Chat with doc
            """
            )
            with gr.Tab("main chat"):
                with gr.Row():
                    with gr.Column():
                        msg = gr.Textbox(label="Question Input", lines=4)
                        system = gr.Textbox(
                            label="(Optional)insturction editing", lines=4
                        )
                        btn = gr.Button("Submit")
                        btnc = gr.ClearButton()
                        btnr = gr.Button("record")

                    output1 = gr.HTML(
                        self.cssa
                        + """
                                        <div class="title">Response</div>
                                            <div class="inner-box">
                                                <div class="content">
                      
                                            """
                        + self.cssb
                    )
                with gr.Row():
                    with gr.Column():
                        # output2 = gr.Textbox(label = "Embedding recall")
                        output2 = gr.HTML(
                            self.cssa
                            + """
                                        <div class="title">Embedding Recall</div>
                                            <div class="inner-box">
                                                <div class="content">
                                    
                                            """
                            + self.cssb
                        )
                    code = gr.HTML(
                        self.cssa
                        + """
                                        <div class="title">Code</div>
                                            <div class="inner-box">
                                                <div class="content">
                                   
                                            """
                        + self.cssb
                    )
                    with gr.Row():
                        with gr.Column():
                            output3 = gr.Textbox(label="key words", lines=2)
                            output4 = gr.Textbox(label="key words code", lines=14)

            btn.click(
                self.wrapper_respond,
                inputs=[msg, system],
                outputs=[msg, output1, output2, output3, code, output4],
            )
            btnc.click(
                self.clean, outputs=[msg, output1, output2, output3, code, output4]
            )
            msg.submit(
                self.wrapper_respond,
                inputs=[msg, system],
                outputs=[msg, output1, output2, output3, code, output4],
            )  # Press enter to submit

        gr.close_all()
        demo.queue().launch(share=False, height=800)


if __name__ == "__main__":

    def respond_function(msg, system):
        RAG = """

        
        """
        return msg, RAG, "Embedding_recall_output", "Key_words_output", "Code_output"

    gradio_interface = GradioInterface(respond_function)
