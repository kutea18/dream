from dream.plugins import plugin
from dream.plugins.TimeSupport import TimeSupportMixin

class PostProcessOrderLateness(plugin.OutputPreparationPlugin, TimeSupportMixin):
  """ Postprocess order lateness for Input_viewResultOrderLateness
  """

  def postprocess(self, data):
    self.initializeTimeSupport(data)
    for result in data['result']['result_list']:
      order_lateness_dict = result[self.configuration_dict["output_id"]] = {}
      for obj in result['elementList']:
        if obj.get('_class') == "Dream.Mould": # XXX How to find orders ?
          orderFound = False
          for order in data['input']['BOM']['productionOrders']:
            for component in order.get('componentsList', []):
              if component.get('id',None) == obj.get('id', None):
                orderFound = True
                break
            if orderFound:
              dueDate = order.get('dueDate', None)
              if obj['results'].get('schedule', []):
                completed = isinstance(obj["results"]["completionTime"], (int, float))
                order_lateness_dict[order['id']] = {
                  'dueDate': self.convertToFormattedRealWorldTime(dueDate),
                  # XXX do we want to format to another time unit ? days ?
                  'delayText': ("%d %s" % (obj["results"]["completionTime"] - dueDate, data['general']['timeUnit'])) if completed else None, # XXX manpy outputs delay, but it is sometimes wrong
                  'delay': obj["results"]["completionTime"] - dueDate if completed else None,
                  'manpy_delay': obj['results'].get('delay'),
                  'completionDate': self.convertToFormattedRealWorldTime(obj["results"]["completionTime"]) if completed else obj["results"]["completionTime"],
                }
                # XXX format delay as number of days.
                if data['general']['timeUnit'] == 'hour' and completed:
                  order_lateness_dict[order['id']]['delayText'] = "%d Days" % ((obj["results"]["completionTime"] - dueDate) / 24.)
              else:
                # if order is not processed at all, it has no schedule.
                order_lateness_dict[order['id']] = {
                  'dueDate': self.convertToFormattedRealWorldTime(dueDate),
                  'delay': 1000,
                  'completionDate': 'Unfinished'
                }
              break
        if obj.get('_class') == "Dream.CapacityProject": # XXX How to find orders ?
          dueDate, = [order['dueDate'] for order in data['input']['BOM']['productionOrders'] if order['id'] == obj['id']]
          if obj["results"]["schedule"]:
            completionTime = obj["results"]["schedule"][-1]["exitTime"]
            order_lateness_dict[obj["id"]] = {
              "dueDate": self.convertToFormattedRealWorldTime(dueDate),
              "delay": completionTime - dueDate,
              "delayText": "%d %s" % (completionTime - dueDate, data['general']['timeUnit']),
              "completionDate": self.convertToFormattedRealWorldTime(completionTime)
            }
          else:
            order_lateness_dict[obj["id"]] = {
              "dueDate": self.convertToFormattedRealWorldTime(dueDate),
              "delay": 1000,
              "completionDate": "Unfinished"
            }

    return data
