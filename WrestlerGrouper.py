import pandas as pd
import numpy as np
import pandas as pd
import os
from scipy.sparse import data
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA

location = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


#Gathers School rosters from Excel file, selects active users
def GatherRoster():
    RosterDict = {}
    for x in TeamList:
        Roster = pd.read_excel(os.path.join(location, 'Wrestlers.xlsx'), sheet_name=x)
        Roster = Roster[Roster["Active"].isin(['Yes'])]
        Roster['School'] = x
        RosterDict[x] = Roster
    return RosterDict

def GatherTeams():
    MeetDict={}
    SessionCount=0
    Meet = pd.read_excel(os.path.join(location, 'Wrestlers.xlsx'), sheet_name='UpcomingMeet')
    SessionList = Meet.columns.tolist()
    SessionNumber=sum('Session' in s for s in SessionList)
    while SessionCount != SessionNumber:
        Team = Meet['Session '+str(SessionCount+1)].tolist()
        MeetDict['Session '+(str(SessionCount+1))]= Team
        SessionCount=SessionCount+1
    return MeetDict

#Returns the Average "Score" for each Group that has been created
def GetScoreAverage(ScoreDict):
    AverageValues={}        
    for x in ScoreDict.keys():
        Average = np.mean(ScoreDict[x])
        AverageValues[x] =int(Average)
    return(AverageValues)

#Splits Dataframe into Groups of 4
def split_dataframe(df, chunk_size = 4): 
    chunks = list()
    num_chunks = len(df) // chunk_size + 1
    for i in range(num_chunks):
        chunks.append(df[i*chunk_size:(i+1)*chunk_size])
    return chunks

def CountOccurences(lst, x):
    count = 0
    for ele in lst:
        if (ele == x):
            count = count + 1
    return count

def GroupingMachine(TotalWrestlers, CombinedRoster):
    count = 1
    GroupDict = {}
    ScoreDict = {}
    RoundedUpGroupNumber = -(-(TotalWrestlers) // 4)
    SacrificialRoster=CombinedRoster
    while count < (RoundedUpGroupNumber+1):
        SacrificialRoster = SacrificialRoster.sort_values(['Score'], ascending=True)
        PotentialPairs = SacrificialRoster.head(4)
        SchoolList= PotentialPairs['School'].tolist()
        UserList = PotentialPairs['ID'].tolist()
        ScoreList = PotentialPairs['Score'].tolist()
        SacrificialRoster=SacrificialRoster[~SacrificialRoster['ID'].isin(UserList)]
        GroupDict[count]= UserList
        ScoreDict[count]= ScoreList
        count= count+1
    return(GroupDict)

def GroupingMachineSchoolComprehension(TotalWrestlers, CombinedRoster):
    count = 1
    GroupDict = {}
    ScoreDict = {}
    RoundedUpGroupNumber = -(-(TotalWrestlers) // 4)
    SacrificialRoster=CombinedRoster
    while count < (RoundedUpGroupNumber+1):
        SacrificialRoster = SacrificialRoster.sort_values(['Score'], ascending=True)
        PotentialPairs = SacrificialRoster.head(4)
        SchoolList= PotentialPairs['School'].tolist()
        for x in SchoolList:
            Occurences = CountOccurences(SchoolList,x)
            checked =0
            checked = checked+1
            attempt = 0
            NewGroup=PotentialPairs
            while Occurences>2:
                CurrentGroup = PotentialPairs.head(3-attempt)
                CurrentSchools = PotentialPairs['School'].tolist()
                PotentialRoster = SacrificialRoster[~SacrificialRoster['School'].isin(CurrentSchools)]
                PotentialRoster = PotentialRoster.head(1+attempt)
                NewGroup = pd.concat([PotentialRoster,CurrentGroup])
                NewGroup['School'].tolist()
                Occurences = CountOccurences(NewGroup['School'].tolist(), x)
                attempt = attempt+1
                if attempt>3:
                    break
            if Occurences <=2 and checked>=1:
                break
        PotentialPairs = NewGroup
        
        UserList = PotentialPairs['ID'].tolist()
        ScoreList = PotentialPairs['Score'].tolist()
        SacrificialRoster=SacrificialRoster[~SacrificialRoster['ID'].isin(UserList)]
        GroupDict[count]= UserList
        ScoreDict[count]= ScoreList
        count= count+1
    return(GroupDict)

def DataFramePolisher(CombinedRoster,Groups):
    new_dic = {}
    for k,v in Groups.items():
        for x in v:
                new_dic.setdefault(x,[]).append(k)
    GroupDF = pd.concat({k: pd.Series(v) for k, v in new_dic.items()}, axis=1).T
    GroupDF.reset_index(inplace=True)
    GroupDF = GroupDF.rename(columns = {'index':'ID'})
    GroupDF.to_csv(os.path.join(location, 'Results.csv'), index=False)
    GroupDF.columns=['ID', 'Group']
    Final = pd.merge(CombinedRoster, GroupDF, how= 'outer', on='ID')
    Final = Final.sort_values(['Group'], ascending=True)
    #Final = Final.drop(columns=['Score','ID'])
    return Final

def main():
#Gather individual School Rosters as well as Combined Roster
#Create "ID" column to track wrestlers through grouping process
    Rosters = GatherRoster()
    CombinedRoster = pd.concat(Rosters, axis=0)
    CombinedRoster.reset_index(inplace= True, drop=True)
    CombinedRoster.reset_index(inplace=True)
    CombinedRoster = CombinedRoster.rename(columns = {'index':'ID'})
    CombinedRoster = pd.DataFrame(CombinedRoster)

#This line can be modified to change the "weight" of different variables
    avgweight = (CombinedRoster['Actual Weight'].mean())
    avgage = (CombinedRoster['Age'].mean())
    CombinedRoster['Score'] = (((CombinedRoster[str('Actual Weight')])**2)/avgweight) + (((CombinedRoster[str('Age')])**2)/avgage)    
   
#Gather total # of wrestlers and # of groups to make
    TotalWrestlers = CombinedRoster['ID'].max() + 1
    Groups = GroupingMachine(TotalWrestlers, CombinedRoster)
    #Groups = GroupingMachineSchoolComprehension(TotalWrestlers, CombinedRoster)

#Inverts Group Dataframe and matches to Roster to add groups Column to roster
    Final = DataFramePolisher(CombinedRoster, Groups)

#Final.to_csv(os.path.join(location, 'Results.csv'), index=False)
    return Final

TeamList=[]
TeamDict = GatherTeams()
FinalDict={}
for x in TeamDict.keys():
    TeamList=TeamDict[x]
    FinalDict[x]=main()
with pd.ExcelWriter('Results.xlsx') as writer:
    for x in FinalDict.keys():
        FinalDict[x].to_excel(writer, sheet_name=x, index=False)
    