
# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'AFTER_TOMORROW AT BEFORE_YESTERDAY DATE_END DAY MINUS MONTH NUMBER OF ON PAST_PHRASE PHRASE PLUS THE TIME TODAY TOMORROW WORD_NUMBER YEAR YESTERDAY\n    date_object :\n    date_object : date_list\n    date_list :  date_list date\n    date_list : date\n    date_list : date_past\n    date_list : in\n    date_list : adder\n    date_list : remover\n    date_list : date_yesterday\n    date_list : date_2moro\n    date_list : date_day\n    date_list : date_end\n    date_list : date_or\n    date_list : date_before_yesterday\n    date_list : date_after_tomorrow\n    \n    date : TIME\n    date : NUMBER TIME\n    date : WORD_NUMBER TIME\n    date : PHRASE TIME\n    date : TIME PHRASE\n    date : NUMBER TIME PHRASE\n    date : WORD_NUMBER TIME PHRASE\n    date : PHRASE TIME PHRASE\n    \n    in : PHRASE NUMBER TIME\n    in : PHRASE WORD_NUMBER TIME\n    \n    adder : PLUS NUMBER TIME\n    adder : PLUS WORD_NUMBER TIME\n    \n    remover : MINUS NUMBER TIME\n    remover : MINUS WORD_NUMBER TIME\n    \n    date_past : NUMBER TIME PAST_PHRASE\n    date_past : WORD_NUMBER TIME PAST_PHRASE\n    \n    date_yesterday : YESTERDAY\n    date_yesterday : YESTERDAY AT NUMBER\n    date_yesterday : YESTERDAY AT WORD_NUMBER\n    \n    date_2moro : TOMORROW\n    date_2moro : TOMORROW AT NUMBER\n    date_2moro : TOMORROW AT WORD_NUMBER\n    \n    date_day : DAY\n    date_day : PHRASE DAY\n    date_day : PAST_PHRASE DAY\n    \n    date_or : PAST_PHRASE TIME\n    \n    date_before_yesterday : BEFORE_YESTERDAY\n    date_before_yesterday : THE BEFORE_YESTERDAY\n    date_before_yesterday : THE TIME BEFORE_YESTERDAY\n    \n    date_after_tomorrow : AFTER_TOMORROW\n    date_after_tomorrow : THE TIME AFTER_TOMORROW\n    \n    date_end : NUMBER DATE_END\n    date_end : THE NUMBER DATE_END\n    date_end : MONTH NUMBER DATE_END\n    date_end : NUMBER DATE_END OF MONTH\n    date_end : ON THE NUMBER DATE_END\n    date_end : MONTH THE NUMBER DATE_END\n    date_end : THE NUMBER DATE_END OF MONTH\n    '
    
_lr_action_items = {'$end':([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,22,23,24,28,29,30,34,35,36,37,38,41,42,43,51,56,57,58,59,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,80,82,83,84,],[-1,0,-2,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13,-14,-15,-16,-32,-35,-38,-42,-45,-3,-20,-17,-47,-18,-19,-39,-40,-41,-43,-17,-18,-21,-30,-22,-31,-23,-24,-25,-26,-27,-28,-29,-33,-34,-36,-37,-48,-44,-46,-49,-50,-52,-51,-53,]),'TIME':([0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,22,23,24,25,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,51,56,57,58,59,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,80,82,83,84,],[15,15,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13,-14,-15,-16,35,37,38,43,-32,-35,-38,52,-42,-45,-3,56,57,38,-20,-17,-47,-18,-19,64,65,-39,-40,-41,66,67,68,69,-43,-17,-18,-21,-30,-22,-31,-23,-24,-25,-26,-27,-28,-29,-33,-34,-36,-37,-48,-44,-46,-49,-50,-52,-51,-53,]),'NUMBER':([0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,18,20,21,22,23,24,25,26,28,29,30,34,35,36,37,38,41,42,43,48,49,51,54,55,56,57,58,59,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,80,82,83,84,],[16,31,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13,-14,-15,-16,39,44,46,-32,-35,-38,50,53,-42,-45,-3,-20,-17,-47,-18,-19,-39,-40,-41,70,72,-43,78,79,-17,-18,-21,-30,-22,-31,-23,-24,-25,-26,-27,-28,-29,-33,-34,-36,-37,-48,-44,-46,-49,-50,-52,-51,-53,]),'WORD_NUMBER':([0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,18,20,21,22,23,24,28,29,30,34,35,36,37,38,41,42,43,48,49,51,56,57,58,59,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,80,82,83,84,],[17,32,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13,-14,-15,-16,40,45,47,-32,-35,-38,-42,-45,-3,-20,-17,-47,-18,-19,-39,-40,-41,71,73,-43,-17,-18,-21,-30,-22,-31,-23,-24,-25,-26,-27,-28,-29,-33,-34,-36,-37,-48,-44,-46,-49,-50,-52,-51,-53,]),'PHRASE':([0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,22,23,24,28,29,30,34,35,36,37,38,41,42,43,51,56,57,58,59,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,80,82,83,84,],[18,33,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13,-14,-15,34,-32,-35,-38,-42,-45,-3,-20,58,-47,61,63,-39,-40,-41,-43,58,61,-21,-30,-22,-31,-23,-24,-25,-26,-27,-28,-29,-33,-34,-36,-37,-48,-44,-46,-49,-50,-52,-51,-53,]),'PLUS':([0,],[20,]),'MINUS':([0,],[21,]),'YESTERDAY':([0,],[22,]),'TOMORROW':([0,],[23,]),'DAY':([0,18,19,],[24,41,42,]),'PAST_PHRASE':([0,35,37,],[19,59,62,]),'THE':([0,26,27,],[25,54,55,]),'MONTH':([0,60,81,],[26,80,84,]),'ON':([0,],[27,]),'BEFORE_YESTERDAY':([0,25,52,],[28,51,75,]),'AFTER_TOMORROW':([0,52,],[29,76,]),'DATE_END':([16,50,53,78,79,],[36,74,77,82,83,]),'AT':([22,23,],[48,49,]),'OF':([36,74,],[60,81,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'date_object':([0,],[1,]),'date_list':([0,],[2,]),'date':([0,2,],[3,30,]),'date_past':([0,],[4,]),'in':([0,],[5,]),'adder':([0,],[6,]),'remover':([0,],[7,]),'date_yesterday':([0,],[8,]),'date_2moro':([0,],[9,]),'date_day':([0,],[10,]),'date_end':([0,],[11,]),'date_or':([0,],[12,]),'date_before_yesterday':([0,],[13,]),'date_after_tomorrow':([0,],[14,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> date_object","S'",1,None,None,None),
  ('date_object -> <empty>','date_object',0,'p_date_object','__init__.py',375),
  ('date_object -> date_list','date_object',1,'p_date_object','__init__.py',376),
  ('date_list -> date_list date','date_list',2,'p_date_list','__init__.py',386),
  ('date_list -> date','date_list',1,'p_date','__init__.py',392),
  ('date_list -> date_past','date_list',1,'p_date','__init__.py',393),
  ('date_list -> in','date_list',1,'p_date','__init__.py',394),
  ('date_list -> adder','date_list',1,'p_date','__init__.py',395),
  ('date_list -> remover','date_list',1,'p_date','__init__.py',396),
  ('date_list -> date_yesterday','date_list',1,'p_date','__init__.py',397),
  ('date_list -> date_2moro','date_list',1,'p_date','__init__.py',398),
  ('date_list -> date_day','date_list',1,'p_date','__init__.py',399),
  ('date_list -> date_end','date_list',1,'p_date','__init__.py',400),
  ('date_list -> date_or','date_list',1,'p_date','__init__.py',401),
  ('date_list -> date_before_yesterday','date_list',1,'p_date','__init__.py',402),
  ('date_list -> date_after_tomorrow','date_list',1,'p_date','__init__.py',403),
  ('date -> TIME','date',1,'p_single_date','__init__.py',414),
  ('date -> NUMBER TIME','date',2,'p_single_date','__init__.py',415),
  ('date -> WORD_NUMBER TIME','date',2,'p_single_date','__init__.py',416),
  ('date -> PHRASE TIME','date',2,'p_single_date','__init__.py',417),
  ('date -> TIME PHRASE','date',2,'p_single_date','__init__.py',418),
  ('date -> NUMBER TIME PHRASE','date',3,'p_single_date','__init__.py',419),
  ('date -> WORD_NUMBER TIME PHRASE','date',3,'p_single_date','__init__.py',420),
  ('date -> PHRASE TIME PHRASE','date',3,'p_single_date','__init__.py',421),
  ('in -> PHRASE NUMBER TIME','in',3,'p_single_date_in','__init__.py',438),
  ('in -> PHRASE WORD_NUMBER TIME','in',3,'p_single_date_in','__init__.py',439),
  ('adder -> PLUS NUMBER TIME','adder',3,'p_single_date_plus','__init__.py',452),
  ('adder -> PLUS WORD_NUMBER TIME','adder',3,'p_single_date_plus','__init__.py',453),
  ('remover -> MINUS NUMBER TIME','remover',3,'p_single_date_minus','__init__.py',466),
  ('remover -> MINUS WORD_NUMBER TIME','remover',3,'p_single_date_minus','__init__.py',467),
  ('date_past -> NUMBER TIME PAST_PHRASE','date_past',3,'p_single_date_past','__init__.py',481),
  ('date_past -> WORD_NUMBER TIME PAST_PHRASE','date_past',3,'p_single_date_past','__init__.py',482),
  ('date_yesterday -> YESTERDAY','date_yesterday',1,'p_single_date_yesterday','__init__.py',490),
  ('date_yesterday -> YESTERDAY AT NUMBER','date_yesterday',3,'p_single_date_yesterday','__init__.py',491),
  ('date_yesterday -> YESTERDAY AT WORD_NUMBER','date_yesterday',3,'p_single_date_yesterday','__init__.py',492),
  ('date_2moro -> TOMORROW','date_2moro',1,'p_single_date_2moro','__init__.py',509),
  ('date_2moro -> TOMORROW AT NUMBER','date_2moro',3,'p_single_date_2moro','__init__.py',510),
  ('date_2moro -> TOMORROW AT WORD_NUMBER','date_2moro',3,'p_single_date_2moro','__init__.py',511),
  ('date_day -> DAY','date_day',1,'p_single_date_day','__init__.py',528),
  ('date_day -> PHRASE DAY','date_day',2,'p_single_date_day','__init__.py',529),
  ('date_day -> PAST_PHRASE DAY','date_day',2,'p_single_date_day','__init__.py',530),
  ('date_or -> PAST_PHRASE TIME','date_or',2,'p_this_or_next_period','__init__.py',555),
  ('date_before_yesterday -> BEFORE_YESTERDAY','date_before_yesterday',1,'p_before_yesterday','__init__.py',579),
  ('date_before_yesterday -> THE BEFORE_YESTERDAY','date_before_yesterday',2,'p_before_yesterday','__init__.py',580),
  ('date_before_yesterday -> THE TIME BEFORE_YESTERDAY','date_before_yesterday',3,'p_before_yesterday','__init__.py',581),
  ('date_after_tomorrow -> AFTER_TOMORROW','date_after_tomorrow',1,'p_after_tomorrow','__init__.py',591),
  ('date_after_tomorrow -> THE TIME AFTER_TOMORROW','date_after_tomorrow',3,'p_after_tomorrow','__init__.py',592),
  ('date_end -> NUMBER DATE_END','date_end',2,'p_single_date_end','__init__.py',601),
  ('date_end -> THE NUMBER DATE_END','date_end',3,'p_single_date_end','__init__.py',602),
  ('date_end -> MONTH NUMBER DATE_END','date_end',3,'p_single_date_end','__init__.py',603),
  ('date_end -> NUMBER DATE_END OF MONTH','date_end',4,'p_single_date_end','__init__.py',604),
  ('date_end -> ON THE NUMBER DATE_END','date_end',4,'p_single_date_end','__init__.py',605),
  ('date_end -> MONTH THE NUMBER DATE_END','date_end',4,'p_single_date_end','__init__.py',606),
  ('date_end -> THE NUMBER DATE_END OF MONTH','date_end',5,'p_single_date_end','__init__.py',607),
]
