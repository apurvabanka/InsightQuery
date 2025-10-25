from langchain.callbacks.base import BaseCallbackHandler

class ThinkingCallbackHandler(BaseCallbackHandler):
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.thinking_steps = []
    
    def on_agent_action(self, action, **kwargs):
        """Called when the agent takes an action"""
        if hasattr(action, 'log') and action.log:
            # Show all verbose output for debugging
            log_text = action.log
            if "Thought:" in log_text:
                # Extract only the thought part
                thought_start = log_text.find("Thought:")
                if thought_start != -1:
                    thought_text = log_text[thought_start:].split("\n")[0]
                    self.thinking_steps.append(thought_text)
                    self.update_display()
    
    def on_agent_finish(self, finish, **kwargs):
        """Called when the agent finishes"""
        if hasattr(finish, 'log') and finish.log:
            log_text = finish.log
            if "Thought:" in log_text:
                thought_start = log_text.find("Thought:")
                if thought_start != -1:
                    thought_text = log_text[thought_start:].split("\n")[0]
                    self.thinking_steps.append(thought_text)
                    self.update_display()
    
    def update_display(self):
        """Update the display with current thinking steps"""
        if self.thinking_steps:
            display_text = "\n\n".join(self.thinking_steps)
            self.placeholder.markdown(display_text) 