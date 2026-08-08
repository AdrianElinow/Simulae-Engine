from datetime import datetime
from NGIN.utilities.lib.ngin_utils import get_unique_strs, normalize_str
from .SimulaeNode import SimulaeNode
from NGIN.utilities.lib.SimulaeConstants import *

class SimulaeEvent(SimulaeNode):
    '''
    Unified 'event' data-structure for social and physical world-events
    '''

    def __init__(self, 
                 id: str,
                 event_class: str,
                 event_type: str,
                 event_subtype: str,
                 start_timestamp: str | None,
                 end_timestamp: str | None,
                 sources: list,
                 targets: list,
                 observers: list,
                 effects):
        
        references = {
            "created_timestamp": str(datetime.now()), # created now
            "event_class": event_class,
            "event_type": event_type,
            "event_subtype": event_subtype,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }

        relations = {
            SRC: {}, # sources -> who/what triggered the event
            TGT: {}, # targets -> who/what was affected & how
            OBS: {}, # observers -> who/what witnessed the event
        }

        super().__init__(
            id, 
            nodetype=EVT,
            references=references,
            relations=relations,
        )

        self.Effects = list(effects or [])
        self.source_ids = get_unique_strs(sources)
        self.target_ids = get_unique_strs(targets)
        self.observer_ids = get_unique_strs(observers)
        self._sync_participant_relations()

    def _sync_participant_relations(self):
        self.Relations[SRC] = {node_id: {} for node_id in self.source_ids}
        self.Relations[TGT] = {node_id: {} for node_id in self.target_ids}
        self.Relations[OBS] = {node_id: {} for node_id in self.observer_ids}

    def add_source(self, node_id: str) -> bool:
        src_id = normalize_str(node_id)
        
        if src_id and src_id not in self.source_ids:
            self.source_ids.append(src_id)
            self._sync_participant_relations()
            return True
        
        return False
    
    def remove_source(self, node_id: str) -> bool:
        src_id = normalize_str(node_id)
        
        if src_id and src_id in self.source_ids:
            self.source_ids.remove(src_id)
            self._sync_participant_relations()
            return True
        
        return False
    
    def add_target(self, node_id: str) -> bool:
        src_id = normalize_str(node_id)
        
        if src_id and src_id not in self.target_ids:
            self.target_ids.append(src_id)
            self._sync_participant_relations()
            return True
        
        return False
    
    def remove_target(self, node_id: str) -> bool:
        src_id = normalize_str(node_id)
        
        if src_id and src_id in self.target_ids:
            self.target_ids.remove(src_id)
            self._sync_participant_relations()
            return True
        
        return False
    
    def add_observer(self, node_id: str) -> bool:
        src_id = normalize_str(node_id)
        
        if src_id and src_id not in self.observer_ids:
            self.observer_ids.append(src_id)
            self._sync_participant_relations()
            return True
        
        return False
    
    def remove_observer(self, node_id: str) -> bool:
        src_id = normalize_str(node_id)
        
        if src_id and src_id in self.observer_ids:
            self.observer_ids.remove(src_id)
            self._sync_participant_relations()
            return True
        
        return False

    def was_observed_by(self, node_id: str) -> bool:
        src_id = normalize_str(node_id)
        
        if src_id and src_id in self.observer_ids:
            return True
        
        return False
    
    def was_perpetrated_by(self, node_id: str) -> bool:
        src_id = normalize_str(node_id)
        
        if src_id and src_id in self.source_ids:
            return True
        
        return False
    
    def was_inflicted_upon(self, node_id: str) -> bool:
        src_id = normalize_str(node_id)
        
        if src_id and src_id in self.target_ids:
            return True
        
        return False
