from BBData import BBData

class VanillaItemSet:

    class Requirement:



        def RL1():
            '''
            RL1 - Stakeholder Need
            Fields:
                Title - Name
                Need - What is needed
                Rationale - Purpose behind need
                Contact/Role - Who/what role sourced this need
            '''
            fields = [BBData.ShortText('Title', ''),
            BBData.LongText('Need', 'As a stakeholder, I need '),
            BBData.LongText('Rationale', 'So that '),
            BBData.ShortText('Contact/Role', '')]

            return BBData.ItemDefinition(fields=[fields], name='RL1 - Stakeholder Need')

        def RL2():
            '''
            RL2 - System Requirement
            Fields:
                Title - Name
                Requirement - Requirement to fulfill
                Rationale - Purpose behind need
                Metric - How this is measured
                Safety Critical - Is this safety critical
            '''
            fields = [BBData.ShortText('Title', ''),
            BBData.LongText('Requirement', 'The system shall '),
            BBData.LongText('Rationale', 'So that '),
            BBData.ShortText('Metric', ''),
            BBData.Checks([(0, '', False)], 'Safety Critical')]

            return BBData.ItemDefinition(fields=[fields], name='RL2 - System Requirement')

    def getVanillaSet():
            col = BBData.ItemTypeCollection()
            col.addRequirement(VanillaItemSet.Requirement.RL1())
            col.addRequirement(VanillaItemSet.Requirement.RL2())
            return col