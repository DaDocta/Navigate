import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import pyttsx3

from utils.google_utils import authenticate_google_drive, search_google_drive
from utils.general_utils import search_local_files
from utils.gpt_utils import init_openai_client, process_results_openai


class ResultGUI:
    def __init__(self, master, results, ai_response=None, speak_results=False):
        self.master = master
        self.speak_results = speak_results
        master.title("Search Results")

        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=80, height=20)
        self.text_area.pack(pady=10, padx=10)

        # Testing
        self.text_area.delete("1.0", tk.END)

        # Display AI response or regular results
        if ai_response:
            self.display_ai_response(ai_response)
        else:
            self.display_results(results)

        self.text_area.config(state=tk.DISABLED)

        # Delay speaking results until the window is populated
        if self.speak_results:
            self.master.after(500, lambda: self.speak_results_function(results, ai_response))

    def display_ai_response(self, ai_response):
        self.text_area.insert(tk.END, f"AI Response:\n{ai_response}\n\n", "ai")
        self.text_area.tag_config("ai", font=("Helvetica", 12, "italic"))

    def display_results(self, results):
        for file, content in results:
            self.text_area.insert(tk.END, f"File: {file}\n", "file")
            self.text_area.insert(tk.END, f"{content}\n\n", "content")
        self.text_area.tag_config("file", font=("Helvetica", 12, "bold"))

    def speak_results_function(self, results, ai_response=None):
        text_to_speak = ai_response if ai_response else "\n".join(
            [f"File: {file}, Content: {content}" for file, content in results]
        )
        engine = pyttsx3.init()
        engine.say(text_to_speak)
        engine.runAndWait()



class SearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Navigate")
        self.client = init_openai_client("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")  # Replace with your OpenAI key

        options_frame = ttk.LabelFrame(root, text="Search Options", padding=10)
        options_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.search_type = tk.StringVar(value="keyword")
        ttk.Radiobutton(options_frame, text="Keyword Search",
                        variable=self.search_type, value="keyword", command=self.update_input_fields).grid(row=0, column=0)
        ttk.Radiobutton(options_frame, text="AI Prompt",
                        variable=self.search_type, value="prompt", command=self.update_input_fields).grid(row=0, column=1)

        self.source = tk.StringVar(value="drive")
        ttk.Radiobutton(options_frame, text="Google Drive",
                        variable=self.source, value="drive").grid(row=1, column=0)
        ttk.Radiobutton(options_frame, text="Local Files",
                        variable=self.source, value="local").grid(row=1, column=1)

        self.speak_results = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Enable Speaking Results", variable=self.speak_results).grid(row=2, column=0, columnspan=2, pady=5)

        self.keyword_label = ttk.Label(root, text="Enter search term:")
        self.keyword_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.search_entry = ttk.Entry(root, width=50)
        self.search_entry.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.prompt_label = ttk.Label(root, text="Enter AI prompt:")
        self.prompt_entry = ttk.Entry(root, width=50)
        self.prompt_label.grid_forget()
        self.prompt_entry.grid_forget()

        ttk.Button(root, text="Search", command=self.search).grid(row=5, column=0, pady=10)
        self.status = ttk.Label(root, text="")
        self.status.grid(row=6, column=0)

    def update_input_fields(self):
        if self.search_type.get() == "keyword":
            self.prompt_label.grid_forget()
            self.prompt_entry.grid_forget()
            self.keyword_label.config(text="Enter search term:")
        else:
            self.keyword_label.config(text="Enter keyword to search for:")
            self.prompt_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
            self.prompt_entry.grid(row=4, column=0, padx=5, pady=5, sticky="w")

    def run_search_thread(self, mode, search_term_final, prompt_for_gpt):
        def search_thread():
            try:
                ai_prompt_selected = mode == "prompt"
                ai_response = None
                results = []

                if self.source.get() == "drive":
                    service = authenticate_google_drive()
                    results = search_google_drive(service, search_term_final, ai_prompt_selected)
                else:
                    results = search_local_files(search_term_final, ai_prompt_selected)

                if ai_prompt_selected:
                    ai_response = process_results_openai(self.client, search_term_final, prompt_for_gpt, "\n".join(text for _, text in results))

                if not results and not ai_response:
                    self.root.after(0, lambda: messagebox.showinfo("Results", "No matches found for your query or prompt."))
                    return

                self.root.after(0, lambda: self.show_results(results, ai_response))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=search_thread, daemon=True).start()

    def search(self):
        mode = self.search_type.get()
        if mode == "keyword":
            search_term_final = self.search_entry.get().strip()
            if not search_term_final:
                messagebox.showerror("Error", "Please enter a search term")
                return
            prompt_for_gpt = None
        else:
            search_term_final = self.search_entry.get().strip()
            prompt_for_gpt = self.prompt_entry.get().strip()
            if not search_term_final or not prompt_for_gpt:
                messagebox.showerror("Error", "Please enter both the search keyword and the AI prompt")
                return

        self.status.config(text="Searching...")
        self.run_search_thread(mode, search_term_final, prompt_for_gpt)

    def show_results(self, results, ai_response=None):
        result_window = tk.Toplevel(self.root)
        ResultGUI(result_window, results, ai_response, speak_results=self.speak_results.get())


def main():
    root = tk.Tk()
    app = SearchGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
