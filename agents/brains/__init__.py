from agents.brains.brain_browser import brain_browser
from agents.brains.brain_os_device import brain_os_device
from agents.brains.brain_big_tasks import brain_big_tasks
from agents.brains.brain_telephony import brain_telephony
from agents.quality_critic import quality_critic
from agents.swarm_harness import swarm_harness

# Register all specialized LLM brains into the Swarm Harness
swarm_harness.register_brain("browser", brain_browser)
swarm_harness.register_brain("os_device", brain_os_device)
swarm_harness.register_brain("big_tasks", brain_big_tasks)
swarm_harness.register_brain("telephony", brain_telephony)
swarm_harness.register_brain("critic", quality_critic)

__all__ = [
    "brain_browser",
    "brain_os_device",
    "brain_big_tasks",
    "brain_telephony",
    "quality_critic",
    "swarm_harness"
]
