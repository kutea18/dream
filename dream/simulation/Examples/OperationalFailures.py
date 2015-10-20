from dream.simulation.imports import Machine, Queue, NonStarvingEntry, Exit, Part, EventGenerator,ExcelHandler, Part  
from dream.simulation.Globals import runSimulation, G
import random
from random import Random
Rnd = Random(3) 

# transition probabilities
p=0.01
g=0.01
r=0.1
f=0.2

# the capacity of B123
capacity=35

class OpQueue(Queue):
    # allow to be locked between the time periods
    def canAccept(self, callerObject=None):
        if self.locked:
            return False
        return Queue.canAccept(self, callerObject)
    
class OpExit(Exit):
    # set numGoodParts=0 at every replication
    def initialize(self):
        self.numGoodParts=0
        Exit.initialize(self)

    # allow to be locked between the time periods    
    def canAccept(self, callerObject=None):
        if self.locked:
            return False
        return True    
    
    # if the status of the entity is 'Good' update numGoodParts
    def getEntity(self):
        activeEntity=Exit.getEntity(self)
        if activeEntity.status=='Good':
            self.numGoodParts+=1
        return activeEntity
    
    # update the GoodExits list
    def postProcessing(self):
        Exit.postProcessing(self, MaxSimtime=1000.1)
        self.GoodExits.append(self.numGoodParts)

class OpMachine(Machine):
    # allow to be locked between the time periods
    # also if there is failure (state=0) do not get new work
    def canAccept(self, callerObject=None):
        if self.locked:
            return False
        if self.state==0:
            return False
        return Machine.canAccept(self, callerObject)   
    
    # set state=1 at the start of each replication
    def initialize(self):
        Machine.initialize(self)
        self.state=1
    
    # if the state is -1 set that the disposed Entity is 'Bad'
    def removeEntity(self, entity):
        activeEntity=Machine.removeEntity(self, entity)
        if self.state==-1:
            activeEntity.status='Bad'
        return activeEntity

# method invoked by the generator at every time period     
def controllerMethod():
    
    # for every machine calculate the state (based on transition probabilities)
    for M in [M1,M2,M3]:
        rn1=createRandomNumber()
        rn2=createRandomNumber()
        if M.state==1:
            if rn1<p:
                M.state=0
            elif rn2<g:
                M.state=-1    
        elif M.state==0:
            if rn1<r:
                M.state=1
        elif M.state==-1:
            if rn1<f:
                M.state=0        
    
    # unlock E and let part get from M3 to E        
    E.locked=False        
    if len(M3.getActiveObjectQueue()) and (not M3.state==0):
        Controller.sendSignal(sender=M3, receiver=E,signal=E.isRequested)
        yield G.env.timeout(0)   
    E.locked=True
    
    # unlock M3 and let part get from B123 to M3        
    M3.locked=False
    if len(B123.getActiveObjectQueue()) and (not M3.state==0):
        Controller.sendSignal(sender=B123, receiver=M3,signal=M3.isRequested)
        yield G.env.timeout(0)  
    M3.locked=True
    
    # unlock B123 and let parts get from M1 and M2 to B123        
    B123.locked=False  
    if ((len(M1.getActiveObjectQueue())) and (not M1.state==0) \
        or ((len(M2.getActiveObjectQueue())) and not M2.state==0))\
            and len(B123.getActiveObjectQueue())<B123.capacity:
        Controller.sendSignal(receiver=B123,signal=B123.isRequested)
        i=0
        while (len(M1.getActiveObjectQueue()) and (not M1.state==0)) \
            or (len(M2.getActiveObjectQueue()) and (not M2.state==0)):
            # print G.env.now, len(M1.getActiveObjectQueue()), M1.state, len(M2.getActiveObjectQueue()), M2.state, len(B123.getActiveObjectQueue())
            yield G.env.timeout(0)
            if len(B123.getActiveObjectQueue())==B123.capacity:
                break    
    B123.locked=True 
    
    # unlock M1 and M2 and let parts get from NS1 to M1 and from NS2 to M2           
    M1.locked=False
    M2.locked=False    
    if len(M1.getActiveObjectQueue())==0:
        Controller.sendSignal(sender=NS1, receiver=M1,signal=M1.isRequested)
    if len(M2.getActiveObjectQueue())==0:
        Controller.sendSignal(sender=NS2, receiver=M2,signal=M2.isRequested)
    while 1:
        yield G.env.timeout(0) 
        if (len(M1.getActiveObjectQueue()) or M1.state==0) \
                 and (len(M2.getActiveObjectQueue()) or M2.state==0):
            M1.locked=True
            M2.locked=True
            break

# returns a number from the uniform distribution (0,1)
def createRandomNumber():
    return Rnd.uniform(0,1)


#define the objects of the model 
NS1=NonStarvingEntry('NS1','Entry1',entityData={'_class':'Dream.Part','status':'Good'})
NS2=NonStarvingEntry('NS2','Entry2',entityData={'_class':'Dream.Part','status':'Good'})
M1=OpMachine('M1','Machine1', processingTime={'Fixed':{'mean':0.1}})
M2=OpMachine('M2','Machine2', processingTime={'Fixed':{'mean':0.1}})
M3=OpMachine('M3','Machine3', processingTime={'Fixed':{'mean':0.1}})
B123=OpQueue('B123','Queue', capacity=capacity)
E=OpExit('E1','Exit')  
Controller=EventGenerator('EV','Controller',start=0,interval=1,method=controllerMethod)

#define predecessors and successors for the objects    
NS1.defineRouting(successorList=[M1])
NS2.defineRouting(successorList=[M2])
M1.defineRouting(predecessorList=[NS1],successorList=[B123])
M2.defineRouting(predecessorList=[NS2],successorList=[B123])
B123.defineRouting(predecessorList=[M1,M2],successorList=[M3])
M3.defineRouting(predecessorList=[B123],successorList=[E])
E.defineRouting(predecessorList=[M3])

# add all the objects to a list
objectList=[NS1,NS2,M1,M2,M3,B123,E,Controller]  

# set all objects locked at beginning
for obj in objectList:
    obj.locked=True

# GoodExits will keep the number of good parts produced in every replication    
E.GoodExits=[]
    
# call the runSimulation giving the objects and the length of the experiment
runSimulation(objectList, 1000, numberOfReplications=50)

#print the results
PRt=sum(E.Exits)/float(len(E.Exits))
PRg=sum(E.GoodExits)/float(len(E.GoodExits))
print E.Exits
print E.GoodExits
print 'PRt=',PRt/float(1000)
print 'PRg=',PRg/float(1000)
