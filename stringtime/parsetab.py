
# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'A AFTER_TOMORROW AM AT BEFORE_YESTERDAY COLON DATE_END DAY MINUS MONTH NUMBER OF ON PAST_PHRASE PHRASE PLUS PM THE TIME TODAY TOMORROW WORD_NUMBER YEAR YESTERDAY\n    date_object :\n    date_object : date_list\n    date_list : date_list date\n    date_list : date\n    date_list : date_past\n    date_list : in\n    date_list : adder\n    date_list : remover\n    date_list : date_yesterday\n    date_list : date_2moro\n    date_list : date_day\n    date_list : date_end\n    date_list : date_or\n    date_list : date_before_yesterday\n    date_list : date_after_tomorrow\n    date_list : date_twice\n    date_list : timestamp\n    \n    timestamp : NUMBER COLON NUMBER\n    timestamp : AT NUMBER COLON NUMBER\n    timestamp : NUMBER COLON NUMBER COLON NUMBER\n    timestamp : AT NUMBER COLON NUMBER COLON NUMBER\n    \n    date : NUMBER\n    date : WORD_NUMBER\n    date : AT NUMBER\n    date : AT WORD_NUMBER\n    date : TIME\n    date : NUMBER TIME\n    date : NUMBER AM\n    date : NUMBER PM\n    date : AT NUMBER AM\n    date : AT NUMBER PM\n    date : WORD_NUMBER TIME\n    date : PHRASE TIME\n    date : TIME PHRASE\n    date : NUMBER TIME PHRASE\n    date : WORD_NUMBER TIME PHRASE\n    date : PHRASE TIME PHRASE\n    \n    date_twice : date date\n    date_twice : date_day date\n    \n    in : PHRASE NUMBER TIME\n    in : PHRASE WORD_NUMBER TIME\n    \n    adder : PLUS NUMBER TIME\n    adder : PLUS WORD_NUMBER TIME\n    \n    remover : MINUS NUMBER TIME\n    remover : MINUS WORD_NUMBER TIME\n    \n    date_past : NUMBER TIME PAST_PHRASE\n    date_past : WORD_NUMBER TIME PAST_PHRASE\n    \n    date_yesterday : YESTERDAY\n    date_yesterday : YESTERDAY AT NUMBER\n    date_yesterday : YESTERDAY AT WORD_NUMBER\n    \n    date_2moro : TOMORROW\n    date_2moro : TOMORROW AT NUMBER\n    date_2moro : TOMORROW AT WORD_NUMBER\n    \n    date_day : DAY\n    date_day : ON DAY\n    date_day : PHRASE DAY\n    date_day : PAST_PHRASE DAY\n    \n    date_or : PAST_PHRASE TIME\n    \n    date_before_yesterday : BEFORE_YESTERDAY\n    date_before_yesterday : THE BEFORE_YESTERDAY\n    date_before_yesterday : THE TIME BEFORE_YESTERDAY\n    \n    date_after_tomorrow : AFTER_TOMORROW\n    date_after_tomorrow : THE TIME AFTER_TOMORROW\n    \n    date_end : NUMBER DATE_END\n    date_end : THE NUMBER DATE_END\n    date_end : MONTH NUMBER DATE_END\n    date_end : NUMBER DATE_END OF MONTH\n    date_end : ON THE NUMBER DATE_END\n    date_end : MONTH THE NUMBER DATE_END\n    date_end : THE NUMBER DATE_END OF MONTH\n    '
    
_lr_action_items = {'$end':([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,20,25,26,27,31,32,33,34,35,38,39,40,41,42,43,45,46,47,48,49,52,53,54,61,64,68,69,70,71,72,74,75,76,77,78,80,81,82,83,84,85,86,87,88,89,90,92,93,94,95,97,99,100,102,103,105,106,],[-1,0,-2,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13,-14,-15,-16,-17,-22,-23,-26,-48,-51,-54,-59,-62,-3,-22,-23,-38,-39,-27,-28,-29,-64,-32,-24,-25,-34,-33,-56,-57,-58,-55,-60,-27,-32,-24,-35,-46,-18,-36,-47,-30,-31,-37,-40,-41,-42,-43,-44,-45,-49,-50,-52,-53,-65,-61,-63,-66,-67,-19,-68,-69,-20,-70,-21,]),'NUMBER':([0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,24,25,26,27,29,30,31,32,33,34,35,36,38,39,40,41,42,43,44,45,46,47,48,49,52,53,54,59,60,61,62,64,67,68,69,70,71,72,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,92,93,94,95,97,98,99,100,102,103,104,105,106,],[17,34,34,-5,-6,-7,-8,-9,-10,34,-12,-13,-14,-15,-16,-17,-22,-23,46,-26,50,55,57,-48,-51,-54,63,66,-59,-62,-3,-22,-23,70,-38,-39,-27,-28,-29,-64,74,-32,-24,-25,-34,-33,-56,-57,-58,87,89,-55,91,-60,96,-27,-32,-24,-35,-46,-18,-36,-47,-30,-31,99,-37,-40,-41,-42,-43,-44,-45,-49,-50,-52,-53,-65,-61,-63,-66,-67,103,-19,-68,-69,-20,106,-70,-21,]),'WORD_NUMBER':([0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,24,25,26,27,31,32,33,34,35,36,38,39,40,41,42,43,45,46,47,48,49,52,53,54,59,60,61,64,68,69,70,71,72,74,75,76,77,78,80,81,82,83,84,85,86,87,88,89,90,92,93,94,95,97,99,100,102,103,105,106,],[18,35,35,-5,-6,-7,-8,-9,-10,35,-12,-13,-14,-15,-16,-17,-22,-23,47,-26,51,56,58,-48,-51,-54,-59,-62,-3,-22,-23,47,-38,-39,-27,-28,-29,-64,-32,-24,-25,-34,-33,-56,-57,-58,88,90,-55,-60,-27,-32,-24,-35,-46,-18,-36,-47,-30,-31,-37,-40,-41,-42,-43,-44,-45,-49,-50,-52,-53,-65,-61,-63,-66,-67,-19,-68,-69,-20,-70,-21,]),'AT':([0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,20,25,26,27,31,32,33,34,35,38,39,40,41,42,43,45,46,47,48,49,52,53,54,61,64,68,69,70,71,72,74,75,76,77,78,80,81,82,83,84,85,86,87,88,89,90,92,93,94,95,97,99,100,102,103,105,106,],[19,36,36,-5,-6,-7,-8,-9,-10,36,-12,-13,-14,-15,-16,-17,-22,-23,-26,59,60,-54,-59,-62,-3,-22,-23,-38,-39,-27,-28,-29,-64,-32,-24,-25,-34,-33,-56,-57,-58,-55,-60,-27,-32,-24,-35,-46,-18,-36,-47,-30,-31,-37,-40,-41,-42,-43,-44,-45,-49,-50,-52,-53,-65,-61,-63,-66,-67,-19,-68,-69,-20,-70,-21,]),'TIME':([0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,20,21,22,25,26,27,29,31,32,33,34,35,37,38,39,40,41,42,43,45,46,47,48,49,50,51,52,53,54,55,56,57,58,61,64,68,69,70,71,72,74,75,76,77,78,80,81,82,83,84,85,86,87,88,89,90,92,93,94,95,97,99,100,102,103,105,106,],[20,20,20,-5,-6,-7,-8,-9,-10,20,-12,-13,-14,-15,-16,-17,40,45,-26,49,54,-48,-51,-54,65,-59,-62,-3,68,69,49,-38,-39,-27,-28,-29,-64,-32,-24,-25,-34,-33,81,82,-56,-57,-58,83,84,85,86,-55,-60,-27,-32,-24,-35,-46,-18,-36,-47,-30,-31,-37,-40,-41,-42,-43,-44,-45,-49,-50,-52,-53,-65,-61,-63,-66,-67,-19,-68,-69,-20,-70,-21,]),'PHRASE':([0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,20,25,26,27,31,32,33,34,35,38,39,40,41,42,43,45,46,47,48,49,52,53,54,61,64,68,69,70,71,72,74,75,76,77,78,80,81,82,83,84,85,86,87,88,89,90,92,93,94,95,97,99,100,102,103,105,106,],[21,37,37,-5,-6,-7,-8,-9,-10,37,-12,-13,-14,-15,-16,-17,-22,-23,48,-48,-51,-54,-59,-62,-3,-22,-23,-38,-39,71,-28,-29,-64,75,-24,-25,-34,80,-56,-57,-58,-55,-60,71,75,-24,-35,-46,-18,-36,-47,-30,-31,-37,-40,-41,-42,-43,-44,-45,-49,-50,-52,-53,-65,-61,-63,-66,-67,-19,-68,-69,-20,-70,-21,]),'PLUS':([0,],[23,]),'MINUS':([0,],[24,]),'YESTERDAY':([0,],[25,]),'TOMORROW':([0,],[26,]),'DAY':([0,21,22,28,],[27,52,53,61,]),'ON':([0,],[28,]),'PAST_PHRASE':([0,40,45,],[22,72,76,]),'THE':([0,28,30,],[29,62,67,]),'MONTH':([0,73,101,],[30,97,105,]),'BEFORE_YESTERDAY':([0,29,65,],[31,64,93,]),'AFTER_TOMORROW':([0,65,],[32,94,]),'AM':([17,34,46,70,],[41,41,77,77,]),'PM':([17,34,46,70,],[42,42,78,78,]),'DATE_END':([17,63,66,91,96,],[43,92,95,100,102,]),'COLON':([17,46,74,99,],[44,79,98,104,]),'OF':([43,92,],[73,101,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'date_object':([0,],[1,]),'date_list':([0,],[2,]),'date':([0,2,3,10,],[3,33,38,39,]),'date_past':([0,],[4,]),'in':([0,],[5,]),'adder':([0,],[6,]),'remover':([0,],[7,]),'date_yesterday':([0,],[8,]),'date_2moro':([0,],[9,]),'date_day':([0,],[10,]),'date_end':([0,],[11,]),'date_or':([0,],[12,]),'date_before_yesterday':([0,],[13,]),'date_after_tomorrow':([0,],[14,]),'date_twice':([0,],[15,]),'timestamp':([0,],[16,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> date_object","S'",1,None,None,None),
  ('date_object -> <empty>','date_object',0,'p_date_object','__init__.py',438),
  ('date_object -> date_list','date_object',1,'p_date_object','__init__.py',439),
  ('date_list -> date_list date','date_list',2,'p_date_list','__init__.py',449),
  ('date_list -> date','date_list',1,'p_date','__init__.py',455),
  ('date_list -> date_past','date_list',1,'p_date','__init__.py',456),
  ('date_list -> in','date_list',1,'p_date','__init__.py',457),
  ('date_list -> adder','date_list',1,'p_date','__init__.py',458),
  ('date_list -> remover','date_list',1,'p_date','__init__.py',459),
  ('date_list -> date_yesterday','date_list',1,'p_date','__init__.py',460),
  ('date_list -> date_2moro','date_list',1,'p_date','__init__.py',461),
  ('date_list -> date_day','date_list',1,'p_date','__init__.py',462),
  ('date_list -> date_end','date_list',1,'p_date','__init__.py',463),
  ('date_list -> date_or','date_list',1,'p_date','__init__.py',464),
  ('date_list -> date_before_yesterday','date_list',1,'p_date','__init__.py',465),
  ('date_list -> date_after_tomorrow','date_list',1,'p_date','__init__.py',466),
  ('date_list -> date_twice','date_list',1,'p_date','__init__.py',467),
  ('date_list -> timestamp','date_list',1,'p_date','__init__.py',468),
  ('timestamp -> NUMBER COLON NUMBER','timestamp',3,'p_timestamp','__init__.py',486),
  ('timestamp -> AT NUMBER COLON NUMBER','timestamp',4,'p_timestamp','__init__.py',487),
  ('timestamp -> NUMBER COLON NUMBER COLON NUMBER','timestamp',5,'p_timestamp','__init__.py',488),
  ('timestamp -> AT NUMBER COLON NUMBER COLON NUMBER','timestamp',6,'p_timestamp','__init__.py',489),
  ('date -> NUMBER','date',1,'p_single_date','__init__.py',512),
  ('date -> WORD_NUMBER','date',1,'p_single_date','__init__.py',513),
  ('date -> AT NUMBER','date',2,'p_single_date','__init__.py',514),
  ('date -> AT WORD_NUMBER','date',2,'p_single_date','__init__.py',515),
  ('date -> TIME','date',1,'p_single_date','__init__.py',516),
  ('date -> NUMBER TIME','date',2,'p_single_date','__init__.py',517),
  ('date -> NUMBER AM','date',2,'p_single_date','__init__.py',518),
  ('date -> NUMBER PM','date',2,'p_single_date','__init__.py',519),
  ('date -> AT NUMBER AM','date',3,'p_single_date','__init__.py',520),
  ('date -> AT NUMBER PM','date',3,'p_single_date','__init__.py',521),
  ('date -> WORD_NUMBER TIME','date',2,'p_single_date','__init__.py',522),
  ('date -> PHRASE TIME','date',2,'p_single_date','__init__.py',523),
  ('date -> TIME PHRASE','date',2,'p_single_date','__init__.py',524),
  ('date -> NUMBER TIME PHRASE','date',3,'p_single_date','__init__.py',525),
  ('date -> WORD_NUMBER TIME PHRASE','date',3,'p_single_date','__init__.py',526),
  ('date -> PHRASE TIME PHRASE','date',3,'p_single_date','__init__.py',527),
  ('date_twice -> date date','date_twice',2,'p_twice','__init__.py',606),
  ('date_twice -> date_day date','date_twice',2,'p_twice','__init__.py',607),
  ('in -> PHRASE NUMBER TIME','in',3,'p_single_date_in','__init__.py',637),
  ('in -> PHRASE WORD_NUMBER TIME','in',3,'p_single_date_in','__init__.py',638),
  ('adder -> PLUS NUMBER TIME','adder',3,'p_single_date_plus','__init__.py',651),
  ('adder -> PLUS WORD_NUMBER TIME','adder',3,'p_single_date_plus','__init__.py',652),
  ('remover -> MINUS NUMBER TIME','remover',3,'p_single_date_minus','__init__.py',665),
  ('remover -> MINUS WORD_NUMBER TIME','remover',3,'p_single_date_minus','__init__.py',666),
  ('date_past -> NUMBER TIME PAST_PHRASE','date_past',3,'p_single_date_past','__init__.py',680),
  ('date_past -> WORD_NUMBER TIME PAST_PHRASE','date_past',3,'p_single_date_past','__init__.py',681),
  ('date_yesterday -> YESTERDAY','date_yesterday',1,'p_single_date_yesterday','__init__.py',689),
  ('date_yesterday -> YESTERDAY AT NUMBER','date_yesterday',3,'p_single_date_yesterday','__init__.py',690),
  ('date_yesterday -> YESTERDAY AT WORD_NUMBER','date_yesterday',3,'p_single_date_yesterday','__init__.py',691),
  ('date_2moro -> TOMORROW','date_2moro',1,'p_single_date_2moro','__init__.py',708),
  ('date_2moro -> TOMORROW AT NUMBER','date_2moro',3,'p_single_date_2moro','__init__.py',709),
  ('date_2moro -> TOMORROW AT WORD_NUMBER','date_2moro',3,'p_single_date_2moro','__init__.py',710),
  ('date_day -> DAY','date_day',1,'p_single_date_day','__init__.py',727),
  ('date_day -> ON DAY','date_day',2,'p_single_date_day','__init__.py',728),
  ('date_day -> PHRASE DAY','date_day',2,'p_single_date_day','__init__.py',729),
  ('date_day -> PAST_PHRASE DAY','date_day',2,'p_single_date_day','__init__.py',730),
  ('date_or -> PAST_PHRASE TIME','date_or',2,'p_this_or_next_period','__init__.py',761),
  ('date_before_yesterday -> BEFORE_YESTERDAY','date_before_yesterday',1,'p_before_yesterday','__init__.py',782),
  ('date_before_yesterday -> THE BEFORE_YESTERDAY','date_before_yesterday',2,'p_before_yesterday','__init__.py',783),
  ('date_before_yesterday -> THE TIME BEFORE_YESTERDAY','date_before_yesterday',3,'p_before_yesterday','__init__.py',784),
  ('date_after_tomorrow -> AFTER_TOMORROW','date_after_tomorrow',1,'p_after_tomorrow','__init__.py',794),
  ('date_after_tomorrow -> THE TIME AFTER_TOMORROW','date_after_tomorrow',3,'p_after_tomorrow','__init__.py',795),
  ('date_end -> NUMBER DATE_END','date_end',2,'p_single_date_end','__init__.py',805),
  ('date_end -> THE NUMBER DATE_END','date_end',3,'p_single_date_end','__init__.py',806),
  ('date_end -> MONTH NUMBER DATE_END','date_end',3,'p_single_date_end','__init__.py',807),
  ('date_end -> NUMBER DATE_END OF MONTH','date_end',4,'p_single_date_end','__init__.py',808),
  ('date_end -> ON THE NUMBER DATE_END','date_end',4,'p_single_date_end','__init__.py',809),
  ('date_end -> MONTH THE NUMBER DATE_END','date_end',4,'p_single_date_end','__init__.py',810),
  ('date_end -> THE NUMBER DATE_END OF MONTH','date_end',5,'p_single_date_end','__init__.py',811),
]
