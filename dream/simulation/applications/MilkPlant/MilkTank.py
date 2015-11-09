# ===========================================================================
# Copyright 2013 University of Limerick
#
# This file is part of DREAM.
#
# DREAM is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DREAM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with DREAM.  If not, see <http://www.gnu.org/licenses/>.
# ===========================================================================
'''
Created on 09 11 2015

@author: George
'''
'''

'''

from dream.simulation.QueueJobShop import QueueJobShop

class MilkTank(QueueJobShop):                                     
    family='Buffer'
    
    def __init__(self, id=None, name=None, capacity=1,**kw):
        QueueJobShop.__init__(self,id,name,capacity)       
        
    def haveToDispose(self, callerObject=None): 
        if len(self.getActiveObjectQueue()):
            requestedVolume=self.getActiveObjectQueue()[0].remainingRoute[0].get('volume',-1)
            totalLiters=self.getTotalLiters()
            if totalLiters<requestedVolume:
                return False
        return QueueJobShop.haveToDispose(self, callerObject)
                
    def getFat(self):
        return self.getTotalFat()/float(self.getTotalLiters())
        
    def getTotalLiters(self):
        totalLiters=0
        for pack in self.getActiveObjectQueue():
            totalLiters+=pack.liters        
        return totalLiters
            
    def getTotalFat(self):
        totalFat=0       
        for pack in self.getActiveObjectQueue():
            totalFat+=pack.fat*pack.liters
        return totalFat      
        
        
        