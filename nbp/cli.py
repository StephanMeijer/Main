import argparse
from multiprocessing import Pipe
from threading import Thread

import nbp.io.output_writers
from nbp.helpers.validation import int_greater_than_zero


class Cli(object):
    def __init__(self):
        entities = {
            'output_writers': nbp.io.output_writers,
            'input_providers': nbp.io.input_providers,
            'modifiers': nbp.modifiers
        }

        for key, module in entities.items():
            mirror = {}

            for _, entity in vars(module).items():
                if hasattr(entity, 'entity_name'):
                    mirror[entity.entity_name] = entity

            setattr(self, key, mirror)

        self.__args = self.get_args()

    def start_application(self):
        max_ticks, max_time = self.__args.max_ticks, self.__args.max_time

        input_provider_class = self.input_providers[self.__args.inputprovider]

        input_provider = input_provider_class(vars(self.__args))
        generator = input_provider.get_generator()

        pipes = []
        
        bundle = ModifierBundle()

        if self.__args.modifier:
            for modifier_name in self.__args.modifier:
                bundle.add_modifier(self.modifiers[modifier_name]())
                
            generator = bundle.get_generator(generator)

        for ow_name in self.__args.outputwriter:
            parent, child = Pipe()

            ow = self.output_writers[ow_name]
            Thread(target=ow, args=(child, vars(self.__args))).start()

            pipes.append(parent)

        for pipe in pipes:
            pipe.send({ 'type': 'start' })

        for state in generator:
            if max_ticks and max_ticks <= state.ticks:
                self.close_application(pipes)
            elif max_time and max_time < state.time:
                self.close_application(pipes)
            else:
                for pipe in pipes:
                    pipe.send({
                        'type': 'data',
                        'data': state
                    })

        self.close_application(pipes)

    def get_args(self):
        parser = argparse.ArgumentParser(description='N-Body Physics Simulator')

        parser.add_argument('--inputprovider', '-i', metavar='ip',
                            type=str, help='Selection of Input Provider.',
                            dest='inputprovider', required=True,
                            choices=list(self.input_providers.keys()))

        parser.add_argument('--outputwriter', '-o', metavar='outputwriter',
                            type=str, help='Selection of Output Writers.',
                            dest='outputwriter', nargs='+', required=True,
                            choices=list(self.output_writers.keys()))

        parser.add_argument('--delta-time', '-dt', metavar='seconds',
                            type=int_greater_than_zero, help='Change in time.',
                            dest='delta_time', required=True)


        parser.add_argument('--modifier', '-m', metavar='modifiers',
                            type=str, help='Selection of modifier(s).',
                            dest='modifier', nargs='*',
                            choices=list(self.modifiers.keys()))

        max_group = parser.add_mutually_exclusive_group()

        max_group.add_argument('--max-ticks', '-t', metavar='ticks',
                               type=int_greater_than_zero, help='Max ticks to calculate.',
                               dest='max_ticks')

        max_group.add_argument('--max-time', '-T', metavar='seconds',
                               type=int_greater_than_zero, help='Max time to calculate.',
                               dest='max_time')

        basic_args, _ = parser.parse_known_args()

        items = [self.input_providers.get(basic_args.inputprovider)]
        items += [self.output_writers.get(key) for key in basic_args.outputwriter]

        for item in items:
            for argument_set in item.get_cli_arguments():
                parser.add_argument(argument_set[0], **argument_set[1])

        return parser.parse_args()

    def close_application(self, pipes):
        for pipe in pipes:
            pipe.send({ 'type': 'end' })

        exit(0)
