import * as React from 'react';
import Button from '@material-ui/core/Button';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import Select from '@material-ui/core/Select';
import {AppliedOperator, Parameter, RequestResult} from '../types';
import {FormControlLabel, Switch, TextField} from '@material-ui/core';

interface AddOperatorState {
  selectedOperator: AppliedOperator;
}
interface AddOperatorProps {
  result: RequestResult;
  handleDialogExecution: (selectedOperator: AppliedOperator) => void;
  closeRecipeDialog: () => void;
}

class AddOperator extends React.PureComponent<
  AddOperatorProps,
  AddOperatorState
> {
  constructor(props: AddOperatorProps) {
    super(props);
    this.state = {
      selectedOperator: {
        operatorName: '',
        operatorIndex: 0,
        columnName: '',
        columnIndex: 0,
        checked: false,
        newColumnName: '',
      },
    };
    this.handleChangeNewColumnName = this.handleChangeNewColumnName.bind(this);
  }
  handleAddOperator(operatorIndex: number) {
    const operatorParameters: Parameter[] = [];
    this.props.result.library?.functions[operatorIndex].parameters.map(para => {
      const parameter: Parameter = para;
      parameter['value'] = String(para.defaultValue);
      operatorParameters.push(parameter);
    });
    this.setState({
      selectedOperator: {
        ...this.state.selectedOperator,
        operatorIndex: operatorIndex,
        operator: this.props.result.library?.functions[operatorIndex],
        parameters: operatorParameters,
      },
    });
  }
  handleAddColumn(columnIndex: number) {
    this.setState({
      selectedOperator: {
        ...this.state.selectedOperator,
        columnIndex: columnIndex,
      },
    });
  }
  handleChangeColumnSources(columnIndex: number) {
    let sources: number[] = [];
    if (
      this.state.selectedOperator.sources &&
      this.state.selectedOperator.sources.length > 0
    ) {
      sources = this.state.selectedOperator.sources;
    }
    sources.push(columnIndex);
    this.setState({
      selectedOperator: {...this.state.selectedOperator, sources: sources},
    });
  }

  handleChangeSwitch(eventName: string, isChecked: boolean) {
    this.setState({
      selectedOperator: {...this.state.selectedOperator, checked: isChecked},
    });
  }
  handleChangeNewColumnName(event: React.ChangeEvent<HTMLInputElement>) {
    const columnName = event.target.value;
    this.setState({
      selectedOperator: {
        ...this.state.selectedOperator,
        newColumnName: columnName,
      },
    });
  }
  handleChangeParameters(
    event: React.ChangeEvent<HTMLInputElement>,
    index: number
  ) {
    const parameterValue = event.target.value;
    if (this.state.selectedOperator.parameters) {
      const updatedParameters = this.state.selectedOperator.parameters;
      updatedParameters[index]['value'] = parameterValue;
      this.setState({
        selectedOperator: {
          ...this.state.selectedOperator,
          parameters: updatedParameters,
        },
      });
    }
  }

  render() {
    const {result} = this.props;
    return (
      <div>
        <div>
          <div>
            <div style={{marginBottom: 12}}>
              Select an operator and a column. The operator will be applied to
              the column values.
            </div>
            <form noValidate>
              <div>
                <InputLabel htmlFor="max-width">Operator</InputLabel>
                <Select
                  autoFocus
                  value={this.state.selectedOperator.operatorIndex}
                  onChange={e => {
                    this.handleAddOperator(e.target.value as number);
                  }}
                >
                  {result.library &&
                    result.library.functions.map((lib, idx) => (
                      <MenuItem key={idx} value={idx}>
                        {lib.name}
                      </MenuItem>
                    ))}
                </Select>
              </div>
              <div style={{marginTop: 6}}>
                {this.state.selectedOperator.operator &&
                this.state.selectedOperator.operator.columns > 1 ? (
                  <>
                    {Array.from(
                      Array(this.state.selectedOperator.operator.columns).keys()
                    ).map((element: number, index: number) => (
                      <div key={element}>
                        <InputLabel key={'input' + element} htmlFor="max-width">
                          Column {element + 1}{' '}
                        </InputLabel>
                        <Select
                          key={'slect' + element}
                          autoFocus
                          value={
                            this.state.selectedOperator.sources
                              ? this.state.selectedOperator.sources[index]
                              : 0
                          }
                          onChange={e => {
                            this.handleChangeColumnSources(
                              e.target.value as number
                            );
                          }}
                        >
                          {result.columns.map((colName, idx) => (
                            <MenuItem key={idx} value={idx}>
                              {colName}
                            </MenuItem>
                          ))}
                        </Select>
                      </div>
                    ))}
                    {this.state.selectedOperator.parameters &&
                      this.state.selectedOperator.parameters.length > 0 && (
                        <>
                          {this.state.selectedOperator.parameters.map(
                            (parameter: Parameter, idx: number) => (
                              <div key={parameter.index}>
                                <InputLabel
                                  key={'input' + parameter.index}
                                  htmlFor="max-width"
                                >
                                  Parameter {parameter.index + 1}{' '}
                                </InputLabel>
                                <TextField
                                  id="outlined-basic"
                                  size="small"
                                  value={
                                    this.state.selectedOperator.parameters
                                      ? this.state.selectedOperator.parameters[
                                          idx
                                        ].value
                                      : ''
                                  }
                                  onChange={(
                                    event: React.ChangeEvent<HTMLInputElement>
                                  ) => this.handleChangeParameters(event, idx)}
                                  label={
                                    parameter.label
                                      ? parameter.label
                                      : parameter.name
                                  }
                                  variant="outlined"
                                />
                              </div>
                            )
                          )}
                        </>
                      )}
                  </>
                ) : (
                  <>
                    <InputLabel htmlFor="max-width">Column</InputLabel>
                    <Select
                      autoFocus
                      value={this.state.selectedOperator.columnIndex}
                      onChange={e => {
                        this.handleAddColumn(e.target.value as number);
                      }}
                    >
                      {result.columns.map((colName, idx) => (
                        <MenuItem key={idx} value={idx}>
                          {colName}
                        </MenuItem>
                      ))}
                    </Select>
                  </>
                )}
              </div>
              <div style={{marginTop: 6}}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={this.state.selectedOperator.checked}
                      size="small"
                      onChange={e => {
                        this.handleChangeSwitch(
                          e.target.name,
                          e.target.checked
                        );
                      }}
                      name="checkedB"
                      color="primary"
                    />
                  }
                  label="Add as a new column"
                />
                {this.state.selectedOperator.checked && (
                  <TextField
                    id="outlined-basic"
                    size="small"
                    value={this.state.selectedOperator.newColumnName}
                    onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                      this.handleChangeNewColumnName(event)
                    }
                    label="Column name"
                    variant="outlined"
                  />
                )}
                {this.state.selectedOperator.operator &&
                  this.state.selectedOperator.operator.columns > 1 &&
                  !this.state.selectedOperator.checked && (
                    <>
                      <InputLabel htmlFor="max-width">Update Column</InputLabel>
                      <Select
                        autoFocus
                        value={this.state.selectedOperator.columnIndex}
                        onChange={e => {
                          this.handleAddColumn(e.target.value as number);
                        }}
                      >
                        {result.columns.map((colName, idx) => (
                          <MenuItem key={idx} value={idx}>
                            {colName}
                          </MenuItem>
                        ))}
                      </Select>
                    </>
                  )}
              </div>
            </form>
          </div>
          <div style={{marginTop: 3}}>
            <Button
              onClick={() => this.props.closeRecipeDialog()}
              color="primary"
            >
              Cancel
            </Button>
            <Button
              onClick={() =>
                this.props.handleDialogExecution(this.state.selectedOperator)
              }
              color="primary"
              autoFocus
            >
              Apply
            </Button>
          </div>
        </div>
      </div>
    );
  }
}

export {AddOperator};
